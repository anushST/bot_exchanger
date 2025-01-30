def sort_number():
    number = input("Введите число: ")
    if not number.isdigit():
        print("Пожалуйста, вводите только цифры.")
        return
    digits = list(number)
    digits_sorted = sorted(digits)
    sorted_number = ''.join(digits_sorted)
    print("Отсортированное число:", sorted_number)


sort_number()
