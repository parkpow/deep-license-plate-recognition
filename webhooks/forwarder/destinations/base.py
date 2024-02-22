class Destination:
    name = "Destination"

    def process(self, source, description, timestamp):
        raise NotImplementedError

    def __init__(self, cli_args):
        pass

    @classmethod
    def create(cls, cli_args):
        return cls(cli_args)

    @staticmethod
    def add_cli_arguments(sub_parsers):
        raise NotImplementedError
