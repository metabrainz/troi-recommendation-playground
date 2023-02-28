from troi import Element, User


class UserListElement(Element):
    '''
        This element is used to pass a provided list of users into the pipeline.

        :param user_list: A list of user_names
    '''

    def __init__(self, user_list):
        super().__init__()
        self.user_list = user_list

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [User]

    def read(self, inputs):
        return [ User(user_name=user_name) for user_name in self.user_list ]
