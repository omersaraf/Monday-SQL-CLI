import json
import sys

from python_graphql_client import GraphqlClient
from prettytable import PrettyTable
import sqlite3

existing_tables = set()


def extract_table_name(sql_query: str) -> str:
    # Split the query into words
    words = sql_query.lower().split()
    # Find the index of the "FROM" keyword
    from_index = words.index("from")
    # Return the word following the "FROM" keyword
    return words[from_index + 1].replace(";", "")


def load_boards(client: GraphqlClient, conn: sqlite3.Connection):
    res = client.execute("""
        query {
            boards(){
                id
                name
                columns {
                    title
                    type
                }   
            }
        }
    """)

    conn.execute("CREATE TABLE boards (id INTEGER PRIMARY KEY, name TEXT)")
    for item in res["data"]["boards"]:
        qry = "INSERT INTO boards (id, name) VALUES (?, ?)".format(**item)
        conn.execute(qry, [item["id"], item["name"]])
    conn.commit()
    existing_tables.add("boards")


def create_board_table(client: GraphqlClient, conn: sqlite3.Connection, board_id):
    res = client.execute("""
        query {{
            boards(ids: {}){{
                columns {{
                    id
                    type
                    title
                }}
                items {{
                    id
                    name
                    group {{
                        id
                    }}
                    column_values {{
                        id,
                        value,
                        type
                    }}
                }}  
            }}
        }}
    """.format(board_id))

    column_names = [col["id"] for col in res["data"]["boards"][0]["columns"] if col["id"] != "name"]

    conn.execute(
        "CREATE TABLE b_{} (id INTEGER PRIMARY KEY, name TEXT, group_name TEXT, board_id INTEGER, {})".format(board_id,
                                                                                                              ",".join(
                                                                                                                  [
                                                                                                                      f'{name.lower()} TEXT'
                                                                                                                      for
                                                                                                                      name
                                                                                                                      in
                                                                                                                      column_names])))

    for item in res["data"]["boards"][0]["items"]:
        col_ids = ["id", "name", "group_name", "board_id"]
        col_values = [
            ("id", item["id"]),
            ("name", item["name"]),
            ("id", item["group"]["id"]),
            ("id", board_id)
        ]
        for col_val in item["column_values"]:
            if col_val["id"] == "name":
                continue
            col_ids.append(col_val["id"])
            col_values.append((col_val["type"], col_val["value"]))

        qry = "INSERT INTO b_{} ({}) VALUES ({})".format(board_id, ",".join(col_ids), ",".join(["?"] * len(col_values)))
        conn.execute(qry, [monday_type_to_sql(typ, val) for typ, val in col_values])
        conn.commit()


def monday_type_to_sql(typ: type, val):
    if val is None:
        return None

    if typ not in {"link", "color", "subtasks"}:
        return val

    val = json.loads(val)
    if typ == "link":
        return f'{val["text"]} ({val["url"]})'

    if typ == "color":
        return val["index"]

    if typ == "subtasks":
        return " ,".join([str(link["linkedPulseId"]) for link in val["linkedPulseIds"]])


def print_table(cursor):
    field_names = [field[0] for field in cursor.description]

    # Create a PrettyTable instance
    table = PrettyTable(field_names)

    # Add the rows to the table
    for row in cursor:
        table.add_row(row)

    print(table)


if __name__ == '__main__':
    token = sys.argv[1]
    client = GraphqlClient(endpoint="https://api.monday.com/v2", headers={"Authorization": token})
    conn = sqlite3.connect(":memory:")

    load_boards(client, conn)

    while True:
        query = input("sql> ")
        if query == 'exit' or query == 'exit()':
            break

        board_id = extract_table_name(query)
        if not board_id.startswith("b_") and board_id != "boards":
            print(f"Unknown board \"{board_id}\"")
            continue
        if board_id not in existing_tables:
            create_board_table(client, conn, board_id.split("b_")[1])
            existing_tables.add(board_id)

        try:
            print_table(conn.execute(query))
        except Exception as e:
            print(e)
            continue
