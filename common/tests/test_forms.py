from django.utils.datastructures import MultiValueDict
from common.forms import ArrayFieldSelectMultiple


def test_array_field_select_multiple_value_from_datadict():
    widget = ArrayFieldSelectMultiple()
    data = MultiValueDict({'field': ['a', 'b']})
    assert widget.value_from_datadict(data, {}, 'field') == 'a,b'
