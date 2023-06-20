import numpy as np
import pandas as pd
import time
import formatting as f


class BookDB:
    __selected = None
    __books_path = 'BX-Books.csv'
    __ratings_path = 'BX-Book-Ratings.csv'

    __k = 5
    __transposed_table = None
    __rating_rest = None
    __books_table_ratings = None

    def __init__(self):
        self.__load()

    def __load(self):
        start = time.time()
        print("Loading data...")
        rating = pd.read_csv(self.__ratings_path, sep=';', on_bad_lines='skip', encoding="Latin-1")
        rating.columns = ['userID', 'ISBN', 'bookRating']

        rating_count = rating.groupby(by=['ISBN'])['bookRating'].count().reset_index().rename(
            columns={'bookRating': 'ratingCount'})

        rating_merged = rating.merge(rating_count, left_on='ISBN', right_on='ISBN')
        rating_popular = rating_merged.query('ratingCount >= 50')

        self.__rating_rest = rating_merged.query('ratingCount < 50')
        self.__transposed_table = rating_popular.pivot(index='ISBN', columns='userID', values='bookRating').fillna(0)

        global_count = rating_count.loc[:, 'ratingCount'].sum()

        rating_average = rating.groupby(by=['ISBN'])['bookRating'].mean().reset_index().rename(
            columns={'bookRating': 'ratingAverage'})

        global_average = rating_average.loc[:, 'ratingAverage'].mean()

        popularity = rating_count.merge(rating_average, left_on='ISBN', right_on='ISBN')
        popularity['Popularity'] = ((popularity['ratingCount'] / global_count) * popularity['ratingAverage'] +
                                    (1 - (popularity['ratingCount'] / global_count)) * global_average) * 10000
        popularity = popularity.drop(columns=['ratingCount', 'ratingAverage'])

        books_table = \
            pd.read_csv(self.__books_path, sep=';', on_bad_lines='skip', encoding="Latin-1", low_memory=False,
                        usecols=['ISBN', 'Book-Title', 'Book-Author', 'Year-Of-Publication', 'Publisher',
                                 'Image-URL-L'])
        books_table.columns = ['ISBN', 'Title', 'Author', 'Year', 'Publisher', 'Image']
        self.__books_table_ratings = books_table.merge(popularity, left_on='ISBN', right_on='ISBN')
        self.__selected = None
        print("Loaded")
        end = time.time()
        print(end - start)

    def recommend(self, book_id=''):
        start = time.time()
        if not book_id:
            if self.__selected is None:
                raise RuntimeError("No book selected\n")
            else:
                book_id = self.__selected['ISBN']

        if book_id in self.__transposed_table.index:
            selected_book = self.__transposed_table.loc[book_id]
            local_transposed_table = self.__transposed_table.drop(index=book_id)

        elif book_id in self.__rating_rest['ISBN'].values:
            book_ratings = self.__rating_rest[self.__rating_rest['ISBN'] == book_id]
            book_transposed = book_ratings.pivot(index='ISBN', columns='userID', values='bookRating')
            book_transposed = book_transposed.reindex(columns=self.__transposed_table.columns.values).fillna(0)
            selected_book = book_transposed.iloc[0]
            local_transposed_table = self.__transposed_table

        else:
            raise RuntimeError("ISBN not valid")

        distances = np.linalg.norm(local_transposed_table - selected_book, axis=1)
        nearest_neighbor_ids = distances.argsort()[:self.__k]

        result = []
        for i in range(0, self.__k):
            result.append(local_transposed_table.index[nearest_neighbor_ids[i]])

        result = self.__info(result)
        print(f"{f.title('Recommendations:')}\n{result}")
        end = time.time()
        print(end - start)

    def __info(self, books):
        if not books:
            return
        if not isinstance(books, list):
            books = [books]

        result = self.__books_table_ratings.loc[self.__books_table_ratings['ISBN'].isin(books)]

        return self.__to_string(result)

    def __to_string(self, books, index=False):
        output = ''
        for ind, row in books.iterrows():
            # output += "\n"
            if index:
                output += f.accent(f"({ind}) ")
            output += f"{row['Title']}" + \
                      f.secondary(" by ") + \
                      f"{row['Author']}\n" + \
                      f.secondary(f"[{row['ISBN']}] ") + \
                      f"{row['Year']}" + \
                      f.secondary(", ") + \
                      f"{row['Publisher']}\n"
        return output

    def __results_page(self, res, ind):
        count = len(res.index)
        last = count // 10 + (count % 10 != 0)
        if ind < 0 or ind >= last:
            raise ValueError()
        page = res.iloc[ind * 10:(ind + 1) * 10]

        print(f.title(f"Page {ind + 1} out of {last}:"))
        print(self.__to_string(page, index=True))

    def reload(self):
        self.__load()

    def select(self, query):
        start = time.time()
        results_table_id = self.__books_table_ratings.loc[self.__books_table_ratings['ISBN'].values == query]
        if not results_table_id.empty:
            self.__selected = results_table_id.iloc[0]
            self.selected()
            end = time.time()
            print(end - start)
            return

        results_table = self.__books_table_ratings.loc[
            self.__books_table_ratings['Title'].str.contains(query, case=False) |
            self.__books_table_ratings['Author'].str.contains(query, case=False)]
        results_table = results_table.sort_values(by=['Popularity'], ascending=False).reset_index(drop=True)
        if results_table.empty:
            end = time.time()
            print(end - start)
            raise RuntimeError('No results found\n')

        current_page = 0
        self.__results_page(results_table, current_page)
        print("Type the index of the book you want to select\n"
              "Type 'previous' and 'next' to navigate results\n"
              "Type 'cancel' to exit")
        end = time.time()
        print(end - start)

        while True:
            # print(page)
            request = input()
            if request == 'cancel':
                print('Select cancelled')
                break

            elif request == 'previous':
                try:
                    self.__results_page(results_table, current_page - 1)
                    current_page -= 1
                except ValueError:
                    print("First page")

            elif request == 'next':
                try:
                    self.__results_page(results_table, current_page + 1)
                    current_page += 1
                except ValueError:
                    print("Last page")

            elif request.isnumeric():
                ind = int(request)
                if len(results_table.index) > ind:
                    self.__selected = results_table.iloc[ind]
                    break
                else:
                    print(f.error("Invalid index"))

            else:
                print(f.error("Invalid request"))

        self.selected()

    def selected(self):
        if self.__selected is None:
            print("[Nothing selected]\n")
        else:
            print(f"{f.title('Selected book:')}\n{self.__selected}\n")

    def clear(self):
        self.__selected = None
        print("Selection cleared\n")
