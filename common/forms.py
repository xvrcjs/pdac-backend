from django import forms
from django.utils.datastructures import MultiValueDict

class ArrayFieldSelectMultiple(forms.SelectMultiple):
    """This is a Form Widget for use with a Postgres ArrayField. It implements
    a multi-select interface that can be given a set of `choices`.

    You can provide a `delimiter` keyword argument to specify the delimeter used.
    """
    template_name = 'admin/widget/array_field_select_multiple.html'
    
    class Media:
        js = ['js/clearable_image_input.js']

    def __init__(self, *args, **kwargs):
        # Accept a `delimiter` argument, and grab it (defaulting to a comma)
        self.delimiter = kwargs.pop("delimiter", ",")
        super(ArrayFieldSelectMultiple, self).__init__(*args, **kwargs)

    def render_options(self, choices, value):
        # value *should* be a list, but it might be a delimited string.
        if isinstance(value, str):  # python 2 users may need to use basestring instead of str
            value = value.split(self.delimiter)
        return super(ArrayFieldSelectMultiple, self).render_options(choices, value)

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            # Normally, we'd want a list here, which is what we get from the
            # SelectMultiple superclass, but the SimpleArrayField expects to
            # get a delimited string, so we're doing a little extra work.
            return self.delimiter.join(data.getlist(name))
        return data.get(name, None)
