import shlex
from bookdb import BookDB
import formatting as f


class App:
    __command_list = (("recommend", 1),
                      ("select <query>", 2),
                      ("selected", 1),
                      ("clear", 1),
                      ("reload", 1))

    __book_db = BookDB()

    def __valid(self, args):
        if args[0] == 'help':
            return True
        if len(args) > 0:
            for c in self.__command_list:
                if c[0].startswith(args[0]) and len(args) >= c[1]:
                    return True
            return False

    def __command(self, c_str):
        args = shlex.split(c_str)
        if self.__valid(args):
            if args[0] == 'help':
                for c in self.__command_list:
                    print(c[0])

            elif self.__command_list[0][0].startswith(args[0]):  # recommend
                self.__book_db.recommend()

            elif self.__command_list[1][0].startswith(args[0]):  # select
                buffer = ''
                for x in args[1:]:
                    buffer += x + ' '
                self.__book_db.select(buffer.rstrip())

            elif self.__command_list[2][0].startswith(args[0]):  # selected
                self.__book_db.selected()

            elif self.__command_list[3][0].startswith(args[0]):  # clear
                self.__book_db.clear()

            elif self.__command_list[4][0].startswith(args[0]):  # clear
                self.__book_db.reload()

        else:
            raise RuntimeError("Invalid command")

    def run(self):
        while True:
            buffer = input()
            if buffer == 'exit':
                break
            try:
                self.__command(buffer)
            except Exception as ft_err:
                print(f.error(f"Error: {ft_err}"))


if __name__ == '__main__':
    app = App()
    try:
        app.run()
    except Exception as err:
        print(f.fatal_error(f"Fatal: {err}"))