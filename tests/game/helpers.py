from mock import MagicMock
from equanimity.helpers import validate_length, atomic
from ..base import BaseTest


class TestHelpers(BaseTest):

    def test_validate_length(self):
        validate_length([1], **dict(min=0, max=10))

    def test_validate_length_invalid(self):
        self.assertExceptionContains(
            ValueError, 'Invalid sequence length', validate_length, [1],
            **dict(min=2, max=4)
        )
        self.assertExceptionContains(
            ValueError, 'Invalid sequence length', validate_length, [1] * 5,
            **dict(min=2, max=4)
        )

    def test_atomic_calls_function(self):
        f = MagicMock(__name__='dog')
        atomic(f)(7)
        f.assert_called_once_with(7)
