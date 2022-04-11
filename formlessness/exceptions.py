from __future__ import annotations

from typing import Iterable, Mapping, Sequence


class ValidationIssue(Exception):
    """
    Validators either passed or they didn't. And if they didn't, what's the message?

    Keep these truthy!
    """


class ValidationIssueMap(Mapping[str, Sequence[ValidationIssue]], ValidationIssue):
    """
    When you want to raise many issues at once.
    """

    @classmethod
    def from_issues(
        cls, key: str, issues: Iterable[ValidationIssue]
    ) -> ValidationIssueMap:
        top_level_issues = []
        sub_issues = {}
        for issue in filter(None, issues):
            if isinstance(issue, ValidationIssueMap):
                sub_issues[issue.key] = issue
            else:
                top_level_issues.append(issue)
        return cls(key, tuple(top_level_issues), sub_issues)

    def __init__(
        self,
        key: str,
        top_level_issues: Iterable[ValidationIssue] = (),
        sub_issues: Mapping[str, ValidationIssueMap] = None,
    ) -> None:
        self.key = key
        self.top_level_issues = (
            top_level_issues
            if isinstance(top_level_issues, tuple)
            else tuple(top_level_issues)
        )
        self.sub_issues = sub_issues or {}

    def add_issues(self, issues: Iterable[ValidationIssue]) -> ValidationIssueMap:
        return self | ValidationIssueMap.from_issues(self.key, issues)

    def __getitem__(self, k: str) -> Sequence[ValidationIssue]:
        head, _, rest = k.partition(".")
        if not head:
            return self.top_level_issues
        return self.sub_issues.get(head, {}).get(rest, ())

    def __len__(self) -> int:
        return len(self.keys())

    def __bool__(self):
        return bool(self.keys())

    def items(self) -> Iterable[tuple[str, Sequence[ValidationIssue]]]:
        if self.top_level_issues:
            yield "", self.top_level_issues
        for k1, sub_issue in self.sub_issues.items():
            for k2, issues in sub_issue.items():
                yield f"{k1}.{k2}" if k2 else k1, issues

    def __iter__(self) -> Iterable[str]:
        for k, v in self.items():
            yield k

    def values(self) -> Iterable[Sequence[ValidationIssue]]:
        for k, v in self.items():
            yield v

    def flat(self) -> Iterable[tuple[str, ValidationIssue]]:
        for k, issues in self.items():
            for issue in issues:
                yield k, issue

    def __or__(self, other: ValidationIssueMap):
        if not isinstance(other, ValidationIssueMap):
            raise NotImplemented
        sub_issues = self.sub_issues.copy()
        for key, issue_map in other.sub_issues.items():
            sub_issues[key] = (
                sub_issues[key] | issue_map if key in sub_issues else issue_map
            )
        return ValidationIssueMap(
            self.key, self.top_level_issues + other.top_level_issues, sub_issues
        )

    def __str__(self) -> str:
        return "\n".join([f"{dot_path}: {issue}" for dot_path, issue in self.flat()])

    def raise_if_not_empty(self) -> None:
        if self:
            raise self
