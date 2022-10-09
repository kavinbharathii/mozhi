import basic

while True:
    text = input("mozhi > ")

    if text == "exit()":
        break

    result, err = basic.run("<stdin>", text)

    if err: print(err.as_string())
    else: print(result)
