"""Script to help convert some ANSI SQL scripts to format suitable for sqlite.

STATUS: COMPLETE but UNTESTED

This expects to input SQL scripts
1) Describes how to alter the table - essenitally which columns are primary key
   and foreign keys
2) Describes how to create the tables - this is missing

The expected output of this script
A single SQL Script which creates the table with primary keys and foreign keys
at the same time.

This uses the sqlparse library (https://sqlparse.readthedocs.io/en/latest/) to
help parse the SQL files.

Completed:
- It support parsing the SQL script that alters the tables to add the primary
  key and foreign key constraints to collect up that information.
- It supports parsing the SQL Script to create the tables and adding the
  primary key to it.
- Adding the foregin key constraints to the CREATE TABLE.
    FOREIGN KEY(column_name) REFERENCES other_table_name(other_column_name)
"""

import sqlparse
import os

BASE_DIRECTORY = r'G:\GeoData\Extracted\G-NAF\Extras\GNAF_TableCreation_Scripts'

SQL_PK_FK_CONSTRAINTS = os.path.join(BASE_DIRECTORY, 'add_fk_constraints.sql')
SQL_CREATE_TABLE = os.path.join(BASE_DIRECTORY, 'create_tables_ansi.sql')


def filter_out_comments(sequence):
    # NOTE: sqlparse has some basic support for handling this.
    for token in sequence:
        if isinstance(token, sqlparse.sql.Comment):
            continue

        if token.is_whitespace:
            continue

        yield token


def match_next_keywords(tokens, keywords):
    # If this doesn't match it means the caller will miss out on that
    # token. It kind of needs to return False and the token.
    for keyword in keywords:
        token = next(tokens)
        if not token.is_keyword:
            return False, token

        if token.value != keyword:
            return False, token

    return True, token


def decode_alter_table(tokens):
    """Decodes an ALTER TABLE statement that is in one of the two expected
    formats. Basically, limited ot looking for adding primary key or foreign
    keys.

    Expected format:
        ALTER TABLE table_name ADD
            CONSTRAINT constraint_name PRIMARY KEY (column_name);
    Alternative format:
        ALTER TABLE table_name ADD
        CONSTRAINT constraint_name FOREIGN KEY (column_name)
        REFERENCES table_name_other (column_name_other);
    """

    tokens = filter_out_comments(tokens)
    first_token = next(tokens)  # Alter
    assert first_token.is_keyword
    token = next(tokens)
    assert token.is_keyword
    assert token.value == 'TABLE'

    # Decode table name.
    token = next(tokens)
    assert not token.is_keyword
    table_name = token.value

    # Check the next two items are the two keywords.
    match_next_keywords(tokens, ['ADD', 'CONSTRAINT'])

    constraint_name = next(tokens).value

    is_primary_key, token = match_next_keywords(tokens, ['PRIMARY', 'KEY'])
    if not is_primary_key:
        # Option 2: 'FOREIGN KEY'
        assert token.is_keyword
        assert token.value == 'FOREIGN'

        token = next(tokens)
        assert token.is_keyword
        assert token.value == 'KEY'
        action = 'declare-foreign-key'

    token = next(tokens)
    assert not token.is_keyword
    column_name = token.value

    if column_name.startswith('(') and column_name.endswith(')'):
        column_name = column_name[1:-1]

    if is_primary_key:
        return {
            'table_name': table_name,
            'column_name': column_name,
            'action': 'make-primary-key',
        }
    else:
        # More to read.
        token = next(tokens)
        assert token.is_keyword
        assert token.value == 'REFERENCES'

        token = next(tokens)
        assert not token.is_keyword
        assert '(' in token.value

        other_table_name, _, other_column_name = token.value.partition('(')
        other_column_name = other_column_name[:-1]  # Remove trailing )

        return {
            'table_name': table_name,
            'column_name': column_name,
            'other_table_name': other_table_name,
            'other_column_name': other_column_name,
            'action': 'declare-foreign-key',
        }


def parse_sql_statements(sql_path):
    with open(sql_path) as reader:
        statements = sqlparse.split(reader)

    for statement in statements:
        if statement:
            parsed = sqlparse.parse(statement)[0]

            statement_type = parsed.get_type()
            if statement_type == 'ALTER':
                yield decode_alter_table(parsed)
            else:
                raise NotImplementedError(statement_type)


def group_actions(actions):
    """Reformat the actions into a format more suitable for apply to an
    existing SQL script that creates tables.
    """

    # Table name to column name.
    primary_keys = {}

    # Table name to list of (column, table, name_in_table)
    foreign_keys = {}

    for action in actions:
        if action['action'] == 'make-primary-key':
            primary_keys[action['table_name']] = action['column_name']
        elif action['action'] == 'declare-foreign-key':
            foreign_keys.setdefault(action['table_name'], []).append(
                (action['column_name'], action['other_table_name'],
                 action['other_column_name'])
            )

    return {
        'primary_keys': primary_keys,
        'foreign_keys': foreign_keys,
    }


def echo_with_modifications(sql_path, changes):
    """Read the given SQL Script at path.

    If changes is empty then the original script should be output.
    """
    with open(sql_path) as reader:
        statements = sqlparse.split(reader)

    primary = sqlparse.sql.Token(sqlparse.tokens.Keyword.PRIMARY, 'PRIMARY')
    key = sqlparse.sql.Token(sqlparse.tokens.Keyword.KEY, 'KEY')

    primary_keys = changes.get('primary_keys', {})

    def until_next_comma(tokens):
        while True:
            token = next(tokens, None)

            if token is None:
                break

            if isinstance(token, sqlparse.sql.IdentifierList):
                previous_token, next_token = token.get_identifiers()
                return next_token

    def apply_changes(parsed):
        tokens = filter_out_comments(parsed.tokens)

        matched, token = match_next_keywords(tokens, ['CREATE', 'TABLE'])
        if not matched:
            raise ValueError(f'Unexpected {token}')

        table_name = next(tokens).value
        table_description = next(tokens)
        assert table_description.is_group

        primary_column = primary_keys.get(table_name, None)
        if primary_column:
            def is_column_primary_key(column_name_token):
                assert isinstance(column_name_token, sqlparse.sql.Identifier)
                column_name = column_name_token.value
                return column_name == primary_column

            def make_column_primary_key(table_description, column_name):
                space = sqlparse.sql.Token(sqlparse.tokens.Whitespace, ' ')

                token_index = table_description.tokens.index(column_name)
                table_description.tokens.insert(token_index + 3, key)
                table_description.tokens.insert(token_index + 3, space)
                table_description.tokens.insert(token_index + 3, primary)
                table_description.tokens.insert(token_index + 3, space)

            if isinstance(table_description, sqlparse.sql.Parenthesis):
                sub_tokens = table_description.get_sublists()
                column_name = next(sub_tokens)

                if is_column_primary_key(column_name):
                    make_column_primary_key(table_description, column_name)

                while True:
                    next_token = until_next_comma(sub_tokens)
                    if next_token is None:
                        break

                    if is_column_primary_key(next_token):
                        make_column_primary_key(table_description, next_token)
            else:
                raise NotImplementedError()

        foreign_keys = changes.get('foreign_keys', {}).get(table_name, [])

        def tokens_from_fk(fk):
            # FOREIGN KEY(column_name)
            # REFERENCES other_table_name(other_column_name)
            space = sqlparse.sql.Token(sqlparse.tokens.Whitespace, ' ')
            foreign = sqlparse.sql.Token(sqlparse.tokens.Keyword.FOREIGN,
                                         'FOREIGN')
            references = sqlparse.sql.Token(sqlparse.tokens.Keyword.REFERENCES,
                                            'REFERENCES')
            key = sqlparse.sql.Token(sqlparse.tokens.Keyword.KEY, 'KEY')

            column_name, other_table_name, other_column_name = fk

            def parens_name(name):
                return sqlparse.sql.Identifier([
                    sqlparse.sql.Token(sqlparse.tokens.Literal, f'({name})')
                    ])

            return [foreign, space, key, parens_name(column_name),
                    space, references, space,
                    sqlparse.sql.Token(sqlparse.tokens.Literal,
                                       other_table_name),
                    parens_name(other_column_name),
                    sqlparse.sql.Token(sqlparse.tokens.Newline, '\n'),
                    ]

        if foreign_keys:
            last = table_description.tokens.pop()
            # The last token will now be a new line so now add a comma to the
            # token before it.
            if table_description.tokens[-2].is_keyword or \
               isinstance(table_description.tokens[-2], sqlparse.sql.Function):
               table_description.tokens.insert(
                    len(table_description.tokens) - 1,
                    sqlparse.sql.Token(sqlparse.tokens.Punctuation, ','))
            else:
                table_description.tokens[-2].value += ','
            for fk in foreign_keys:
                table_description.tokens.extend(tokens_from_fk(fk))
            table_description.tokens.append(last)

        return parsed

    for statement in statements:
        if statement:
            parsed = sqlparse.parse(statement)[0]
            if parsed.get_type() == 'CREATE':
                print(apply_changes(parsed))
            else:
                print(parsed)
        else:
            print(statement)


if __name__ == '__main__':
    changes = group_actions(parse_sql_statements(SQL_PK_FK_CONSTRAINTS))
    echo_with_modifications(SQL_CREATE_TABLE, changes)
