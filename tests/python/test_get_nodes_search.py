"""The two ways ``get_nodes`` used to answer a question nobody asked.

``get_nodes`` is the discovery call: an agent asks a COMP for its children,
optionally filtered by a name pattern, and builds the next request from what
comes back. Two defects made that answer wrong without saying so.

The pattern path called ``findChildren(name=pattern)`` with no ``depth``, so
it walked the whole subtree — grandchildren and deeper — while the no-pattern
path beside it passed ``depth=1``. Same call, same promise ("the nodes under
this parent"), two different sets, decided only by whether the caller happened
to pass a pattern. The fix passes ``depth=1`` on both paths.

Neither path checked that the parent was a COMP before calling
``findChildren`` on it. A TOP or a CHOP has no children, so the call could not
succeed; the fix returns the error the caller can act on instead of leaving it
to TouchDesigner.

Both tests here fail against the unfixed service: the pattern one returns the
grandchild, the non-COMP one does not reach ``error_result`` at all.
"""

import pytest

from mcp.services.api_service import TouchDesignerApiService

PARENT = "/project1/parent"


def names(result):
	"""The names returned by a successful ``get_nodes`` call."""

	assert result["success"] is True, result
	return [node["name"] for node in result["data"]["nodes"]]


@pytest.fixture
def service():
	return TouchDesignerApiService()


class TestAPatternStaysOneLevelDeep:
	"""A pattern narrows a level; it does not widen the search."""

	def test_a_pattern_does_not_reach_a_grandchild(self, service, scene):
		scene(
			PARENT,
			ops=(
				f"{PARENT}/kick",
				f"{PARENT}/snare",
				# A grandchild under snare whose *name* also matches the glob,
				# so the unfixed call (no depth) returns it two levels down
				# and this assertion is the one that catches it. A grandchild
				# named "tail" would not — the glob is matched against the
				# name, not the path.
				f"{PARENT}/snare/snare_deep",
			),
		)

		assert names(service.get_nodes(PARENT, pattern="snare*")) == ["snare"]

	def test_no_pattern_also_stays_one_level(self, service, scene):
		# The control for the test above: the path that already passed
		# depth=1 must keep behaving identically, so the fix is a match and
		# not a swap.
		scene(
			PARENT,
			ops=(f"{PARENT}/kick", f"{PARENT}/snare", f"{PARENT}/snare/snare_deep"),
		)

		assert names(service.get_nodes(PARENT)) == ["kick", "snare"]

	def test_a_pattern_that_matches_nothing_is_an_empty_list(self, service, scene):
		# Not an error: "nothing here" and "wrong parent" are different
		# answers, and this pins that the depth change did not blur them.
		scene(PARENT, ops=(f"{PARENT}/kick",))

		assert names(service.get_nodes(PARENT, pattern="nope*")) == []


class TestAParentThatCannotHaveChildren:
	"""``findChildren`` on a non-COMP cannot work, so it is refused up front."""

	def test_a_top_parent_is_reported_as_not_a_comp(self, service, scene):
		scene(PARENT, op_type="constantTOP")

		result = service.get_nodes(PARENT)

		assert result["success"] is False, result
		assert result["error"] == (
			f"Parent node is not a COMP and has no children: {PARENT}"
		)

	def test_the_refusal_does_not_depend_on_the_pattern(self, service, scene):
		# Both search paths call findChildren, so both must be guarded — an
		# early return on one branch only would leave the other reachable.
		scene(PARENT, op_type="noiseCHOP")

		assert service.get_nodes(PARENT, pattern="x*")["success"] is False
