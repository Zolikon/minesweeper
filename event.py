class EventHandler:
    registered = []
    handlers = {}

    def __init__(self):
        pass

    @classmethod
    def register(cls):
        def custom_decorator(inner_cls):
            class ModifiedClass(inner_cls):

                def __init__(self, *args, **kw_args):
                    super().__init__(*args, **kw_args)
                    cls.registered.append(self)

                @staticmethod
                def emit_event(event, *args, **kwargs):
                    try:
                        for i in cls.registered:
                            if hasattr(i, 'receive_event'):
                                i.receive_event(event, *args, **kwargs)
                    except RuntimeError as error:
                        if 'Internal C++ object' not in error.__str__():
                            raise error

                def receive_event(self, event, *args, **kwargs):
                    try:
                        if event in cls.handlers:
                            for i in cls.handlers[event]:
                                if hasattr(self, i):
                                    getattr(self, i)(*args, **kwargs)
                    except RuntimeError as error:
                        if 'Internal C++ object' not in error.__str__():
                            raise error

                def unregister(self):
                    if self in cls.registered:
                        cls.registered.remove(self)

                def __del__(self):
                    self.unregister()

            return ModifiedClass

        return custom_decorator

    @classmethod
    def capture_event(cls, event):
        def external(method):
            if event in cls.handlers:
                cls.handlers[event].append(method.__name__)
            else:
                cls.handlers[event] = [method.__name__]

            def internal(*args, **kwargs):
                return method(*args, **kwargs)

            return internal

        return external
