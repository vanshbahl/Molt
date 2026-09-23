"""Deterministic LibCST rewrites for matched sites.

Two responsibilities:

* ``plan_call_edits``: the pure function that applies a replace_call's
  argument edits to one ``cst.Call``. The matcher calls it on the original
  node to decide change-vs-abstain; the transformer calls it again on the
  (possibly child-updated) node to build the output. Either every edit
  applies or an :class:`Unsafe` reason is returned: edits are atomic.
* ``SiteRewriter``: a CSTTransformer that replaces exactly the nodes the
  matcher approved, leaving every other byte of the module untouched.
"""

from __future__ import annotations

import json
from typing import Callable, Union

import libcst as cst
from libcst import MaybeSentinel

from .models import ArgumentEdit, RenameSymbol, ReplaceCall, TypedValue


class Unsafe(str):
    """An abstention reason (a str subclass so it can be reported directly)."""


# --------------------------------------------------------------------------
# Expression helpers
# --------------------------------------------------------------------------


def is_side_effect_free(node: cst.BaseExpression) -> bool:
    """Conservative: literals, bare names, and not/-/+ of those only.

    Attribute access is excluded because properties/descriptors can run code;
    moving such an expression could change evaluation order.
    """
    if isinstance(node, (cst.Name, cst.Integer, cst.Float, cst.Imaginary, cst.SimpleString)):
        return True
    if isinstance(node, cst.ConcatenatedString):
        return is_side_effect_free(node.left) and is_side_effect_free(node.right)
    if isinstance(node, cst.UnaryOperation) and isinstance(node.operator, (cst.Not, cst.Minus, cst.Plus)):
        return is_side_effect_free(node.expression)
    return False


def string_literal_value(node: cst.BaseExpression):
    """Evaluated value of a plain string literal, else None."""
    if isinstance(node, cst.SimpleString) and "f" not in node.prefix.lower() and "b" not in node.prefix.lower():
        return node.evaluated_value
    return None


def render_value(value: TypedValue) -> cst.BaseExpression:
    if value.type == "bool":
        return cst.Name("True" if value.value else "False")
    if value.type == "none":
        return cst.Name("None")
    if value.type == "int":
        literal = cst.Integer(str(abs(value.value)))
        return cst.UnaryOperation(cst.Minus(), literal) if value.value < 0 else literal
    if value.type == "str":
        return cst.SimpleString(json.dumps(value.value))
    raise AssertionError(f"unknown typed value {value.type!r}")


def _quote_for(elements) -> str:
    for el in elements:
        if isinstance(el, cst.DictElement) and isinstance(el.key, cst.SimpleString):
            return el.key.quote[0]
    return '"'


def _string_key(key: str, quote: str) -> cst.SimpleString:
    return cst.SimpleString(f"{quote}{key}{quote}")  # key is an identifier per schema


# --------------------------------------------------------------------------
# Argument list surgery (formatting-preserving)
# --------------------------------------------------------------------------


def _keyword_index(args, keyword: str):
    for i, arg in enumerate(args):
        if arg.keyword is not None and arg.keyword.value == keyword:
            return i
    return None


def remove_arg(args: list, idx: int) -> list:
    removed = args[idx]
    out = args[:idx] + args[idx + 1 :]
    if idx != len(args) - 1 or not out:
        return out
    prev = out[-1]
    if isinstance(removed.comma, cst.Comma):
        # Removed arg had a trailing comma (multi-line call): the previous arg
        # keeps its comma/comment but inherits the closing-paren whitespace.
        trailing = removed.comma.whitespace_after
        ws = prev.comma.whitespace_after
        if isinstance(ws, cst.ParenthesizedWhitespace) and isinstance(trailing, cst.ParenthesizedWhitespace):
            ws = ws.with_changes(indent=trailing.indent, last_line=trailing.last_line)
        else:
            ws = trailing
        out[-1] = prev.with_changes(comma=prev.comma.with_changes(whitespace_after=ws))
    else:
        ws = prev.comma.whitespace_after if isinstance(prev.comma, cst.Comma) else None
        if isinstance(ws, cst.ParenthesizedWhitespace) and ws.first_line.comment is not None:
            # Keep the comma so its comment survives; trailing commas are legal.
            out[-1] = prev.with_changes(whitespace_after_arg=removed.whitespace_after_arg)
        else:
            out[-1] = prev.with_changes(comma=MaybeSentinel.DEFAULT, whitespace_after_arg=removed.whitespace_after_arg)
    return out


def append_arg(args: list, new: cst.Arg) -> list:
    if not args:
        return [new]
    last = args[-1]
    if isinstance(last.comma, cst.Comma):
        sep = args[-2].comma if len(args) >= 2 else cst.Comma(whitespace_after=cst.SimpleWhitespace(" "))
        return args[:-1] + [last.with_changes(comma=sep), new.with_changes(comma=last.comma)]
    return args[:-1] + [last.with_changes(comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(" "))), new]


def append_dict_element(d: cst.Dict, element: cst.DictElement) -> cst.Dict:
    elements = list(d.elements)
    if not elements:
        return d.with_changes(elements=[element])
    last = elements[-1]
    if isinstance(last.comma, cst.Comma):
        sep = elements[-2].comma if len(elements) >= 2 else cst.Comma(whitespace_after=d.lbrace.whitespace_after)
        elements = elements[:-1] + [last.with_changes(comma=sep), element.with_changes(comma=last.comma)]
    else:
        elements = elements[:-1] + [last.with_changes(comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(" "))), element]
    return d.with_changes(elements=elements)


# --------------------------------------------------------------------------
# Edit application
# --------------------------------------------------------------------------


def _apply_edit(args: list, edit: ArgumentEdit) -> Union[list, Unsafe]:
    idx = _keyword_index(args, edit.keyword)

    if edit.kind == "add_keyword":
        if idx is not None:
            return args  # already present: no-op
        return append_arg(args, cst.Arg(value=render_value(edit.value), keyword=cst.Name(edit.keyword),
                                        equal=cst.AssignEqual(cst.SimpleWhitespace(""), cst.SimpleWhitespace(""))))

    if idx is None:
        return args  # nothing to do for this edit at this site

    arg = args[idx]
    if edit.kind == "rename_keyword":
        if _keyword_index(args, edit.new_keyword) is not None:
            return Unsafe(f"call already passes {edit.new_keyword}=; renaming {edit.keyword}= would duplicate it")
        return args[:idx] + [arg.with_changes(keyword=cst.Name(edit.new_keyword))] + args[idx + 1 :]

    if edit.kind == "remove_keyword":
        if not is_side_effect_free(arg.value):
            return Unsafe(f"{edit.keyword}= value may have side effects; removing it would change behaviour")
        return remove_arg(args, idx)

    if edit.kind == "move_keyword_into_dict":
        target_idx = _keyword_index(args, edit.dict_keyword)
        if target_idx is None:
            # Replace in place: same position, so evaluation order is unchanged.
            quote = '"'
            new_dict = cst.Dict([cst.DictElement(_string_key(edit.dict_key, quote), arg.value)])
            return args[:idx] + [arg.with_changes(keyword=cst.Name(edit.dict_keyword), value=new_dict)] + args[idx + 1 :]
        if edit.when_dict_exists == "abstain":
            return Unsafe(f"call already passes {edit.dict_keyword}= and the rule says to abstain")
        existing = args[target_idx].value
        if not isinstance(existing, cst.Dict):
            return Unsafe(f"{edit.dict_keyword}= is not a dict literal; cannot merge {edit.dict_key!r} safely")
        for el in existing.elements:
            if not isinstance(el, cst.DictElement):
                return Unsafe(f"{edit.dict_keyword}= dict contains ** unpacking; key conflicts cannot be ruled out")
            key = string_literal_value(el.key)
            if key is None:
                return Unsafe(f"{edit.dict_keyword}= dict has a non-literal key; key conflicts cannot be ruled out")
            if key == edit.dict_key:
                return Unsafe(f"{edit.dict_keyword}= already sets {edit.dict_key!r}; conflicting values")
        if not is_side_effect_free(arg.value):
            return Unsafe(f"{edit.keyword}= value is not side-effect free; moving it would change evaluation order")
        element = cst.DictElement(_string_key(edit.dict_key, _quote_for(existing.elements)), arg.value)
        merged = args[target_idx].with_changes(value=append_dict_element(existing, element))
        args = args[:target_idx] + [merged] + args[target_idx + 1 :]
        return remove_arg(args, idx)

    raise AssertionError(f"unknown edit kind {edit.kind!r}")


def plan_call_edits(call: cst.Call, op: ReplaceCall) -> Union[cst.Call, Unsafe]:
    """Apply all of ``op``'s edits to ``call`` atomically, or explain why not."""
    if any(arg.star == "**" for arg in call.args):
        return Unsafe("call uses **kwargs; the affected keywords may be hidden inside it")
    args = list(call.args)
    for edit in op.argument_edits:
        result = _apply_edit(args, edit)
        if isinstance(result, Unsafe):
            return result
        args = result
    return call.with_changes(args=args)


# --------------------------------------------------------------------------
# Rewriter
# --------------------------------------------------------------------------


class SiteRewriter(cst.CSTTransformer):
    """Replace approved nodes; ``rewrites`` maps original node -> fn(updated)."""

    def __init__(self, rewrites: dict):
        super().__init__()
        self.rewrites = rewrites
        self.produced = {}

    def on_leave(self, original_node, updated_node):
        fn: Callable = self.rewrites.get(id(original_node))
        if fn is None:
            return updated_node
        new = fn(updated_node)
        self.produced[id(original_node)] = new
        return new


def rewrite_functions(op, decision) -> dict:
    """Map id(node) -> fn(updated_node) for one approved decision."""
    node = decision.node
    if isinstance(op, RenameSymbol):
        new = op.new_attr
        if isinstance(node, cst.Attribute):
            fns = {id(node): lambda upd: upd.with_changes(attr=upd.attr.with_changes(value=new))}
        elif isinstance(node, cst.ImportAlias):
            fns = {id(node): lambda upd: upd.with_changes(name=upd.name.with_changes(value=new))}
        else:  # pragma: no cover
            raise AssertionError(f"rename_symbol cannot rewrite {type(node).__name__}")
        for ref in decision.extra_nodes:
            fns[id(ref)] = lambda upd: upd.with_changes(value=new)
        return fns
    if isinstance(op, ReplaceCall):
        def rebuild(upd):
            planned = plan_call_edits(upd, op)
            if isinstance(planned, Unsafe):  # structure changed under us: refuse loudly
                raise RuntimeError(f"edit plan became unsafe during rewrite: {planned}")
            return planned
        return {id(node): rebuild}
    raise AssertionError(f"operation {op.op!r} never rewrites")
