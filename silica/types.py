class IO:
    def __getitem__(self, index):
        pass

Output = IO()
Input = IO()

class _IO:
    def __init__(self, width=1):
        self._value = 0
        self.width = width

    @property
    def value(self):
        if self.width > 1:
            val = []
            _val = self._value
            for i in range(0, self.width):
                val.insert(0, _val & 1)
                _val >>= 1
            return val
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class Output_(_IO):
    pass

class Input_(_IO):
    pass
