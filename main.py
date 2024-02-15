transform_table = [[12, 4, 6, 2, 10, 5, 11, 9, 14, 8, 13, 7, 0, 3, 15, 1],
                   [6, 8, 2, 3, 9, 10, 5, 12, 1, 14, 4, 7, 11, 13, 0, 15],
                   [11, 3, 5, 8, 2, 15, 10, 13, 14, 1, 7, 4, 12, 9, 6, 0],
                   [12, 8, 2, 1, 13, 4, 15, 6, 7, 0, 10, 5, 3, 14, 9, 11],
                   [7, 15, 5, 10, 8, 1, 6, 13, 0, 9, 3, 14, 11, 4, 2, 12],
                   [5, 13, 15, 6, 9, 2, 12, 10, 11, 7, 8, 1, 4, 3, 14, 0],
                   [8, 14, 2, 5, 6, 9, 1, 12, 15, 4, 11, 0, 13, 10, 3, 7],
                   [1, 7, 14, 13, 0, 5, 8, 3, 4, 15, 10, 6, 9, 12, 11, 2]]


# Входной блок длиной 32 бита, выходной блок длиной 32 бита
def t(input_block):
    """Функция нелинейного биективного преобразования"""

    # print(bin(input_block & 0xffffffff))
    output_block = 0

    for i in reversed(range(8)):

        # Сдвигаем биты слева (заполняем 0 правую часть для 4 бит), чтобы освободить место для следующего фрагмента
        output_block <<= 4
        # print('output_block =', output_block, bin(output_block & (2**32 - 1)))

        # Собираемся получить доступ к 4 битам входного блока,
        # делаем это, сдвигая блок право на 4*i бит (заполняем нулями 4*i бит слева)
        # 0xf - побитовая маска 00001111, т.е. результат операции - значение, содержащее 4 младших
        # бита из блока, полученного с помощью сдвига
        # Таким образом, конструкция позволяет извлекать четыре бита из блока длиной 32 бита, начиная с i-го блока,
        # print('i =', i)
        j = (input_block >> (4 * i)) & 0xf
        # print('input_block >> 4 * i =', bin((input_block >> 4 * i) & 0xf))
        # print('j =', j)

        # XOR с элементом таблицы
        output_block ^= transform_table[i][j]
        # print('output_block =', output_block, bin(output_block & (2**32 - 1)))

    return output_block

# input_block = int('fdb97531', 16)
# print(hex(t(input_block)))


def shift_11bits(input_block):
    """Функция циклического сдвига влево на 11 разрядов (битов)"""
    # Биты, вышедшие за пределы перемещаются к правому концу и XOR со сдвинутыми влево битами
    return ((input_block << 11) ^ (input_block >> 21)) & (2**32 - 1)


def g(input_block, key):
    """Функция Фейстеля"""
    # Взятие по модулю 2**32
    return shift_11bits(t((input_block + key) % 2**32))

input_block = int('87654321', 16)
key = int('fedcba98', 16)
print(input_block + key)
print((input_block + key) % 2**32)
print(t((input_block + key) % 2**32))
print(g(input_block, key))


def separation_block(input_block):
    """Функция разбиения 64-битного блока на левую и правую 32-битную часть"""
    return (input_block >> 32, input_block & (2**32 - 1))


def combining_blocks(left, right):
    """Функция объединения двух 32-битных блоков"""
    # Освобождение 32 мест справа (заполнение этих мест нулями)
    return (left << 32) ^ right


# key - 256 битовый ключ, keys - массив, состоящий из 32 32-битовых ключей
def key_deployment_alg(key):
    """Функция развертывания ключа"""
    keys = []

    # Формирование первых 8 уникальных ключей (32-битные блоки, идущие с начала ключа key)
    for i in reversed(range(8)):
        keys.append((key >> (32 * i)) & (2**32 - 1))

    # Формирование следующих 16 ключей (повторение первых 8)
    for j in range(2):
        for i in range(8):
            keys.append(keys[i])

    # Формирование следующих 8 ключей (повторение первых 8 в обратном порядке)
    for i in reversed(range(8)):
        keys.append(keys[i])
    return keys

# key = int('ffeeddccbbaa99887766554433221100f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff', 16)
# print([hex(ki) for ki in key_deployment_alg(key)])


# input_block - открытый текст длиной 64 бита, key - ключ длиной 256 бит, возврат - шифртекст длиной 64 бита
def magma_encrypt(input_block, key):
    """Функция зашифрования 64-битного блока шифром Магма"""

    # Развертывание ключа
    keys = key_deployment_alg(key)

    # Разбиение 64-битного блока на два 32-битных блока
    (left, right) = separation_block(input_block)

    # Реализация первых 31 раундов шифрования
    for i in range(31):
        (left, right) = (right, left ^ g(right, keys[i]))  # Реализация функции G[key],т.е. проход по схеме Фейстеля

    # Реализация последнего 32-го раунда, оставляя 32-битные блоки на месте
    return combining_blocks(left ^ g(right, keys[-1]), right)

# message = int(input(), 16)
# key = int(input(), 16)
# print(hex(magma_encrypt(message, key)))


def magma_decrypt(input_block, key):
    """Функция расшифрования 64-битного блока шифром Магма"""
    # Развертывание ключа
    keys = key_deployment_alg(key)

    # Реверсивное преобразование ключей для расшифрования
    keys.reverse()

    # Разбиение 64-битного блока на два 32-битных блока
    (left, right) = separation_block(input_block)

    # Реализация первых 31 раундов шифрования
    for i in range(31):
        (left, right) = (right, left ^ g(right, keys[i]))  # Реализация функции G[key],т.е. проход по схеме Фейстеля

    # Реализация последнего 32-го раунда, оставляя 32-битные половины на месте
    return combining_blocks(left ^ g(right, keys[-1]), right)


def read_file_and_split(filename):
    # Открываем файл для чтения
    with open(filename, 'r') as file:
        # Читаем строки из файла
        lines = file.readlines()

    # Создаем список для хранения блоков
    blocks = []

    # Обрабатываем каждую строку
    for line in lines:
        # Удаляем символы переноса строки
        line = line.strip()
        # Разбиваем строку на блоки по 64 бита
        for i in range(0, len(line), 16):
            block = line[i:i + 16]
            blocks.append(block)

    return blocks


key = int(input("Введите ключ длиной 256 бит: "), 16)

action = int(input("Выберите: \n"
               "1 Зашифрование открытого текста шифром Магма \n"
               "2 Расшифрование шифртекста шифром Магма \n"))

input_filename = 'input.txt'
output_filename = 'output.txt'

blocks = read_file_and_split(input_filename)

if action == 1:
    with open(output_filename, 'w') as output_file:
        # Записываем блоки в файл
        for block in blocks:
            output_file.write(hex(magma_encrypt(int(block, 16), key))[2:])
        print("Зашифрованный текст находится в файле output.txt")
else:
    with open(output_filename, 'w') as output_file:
        # Записываем блоки в файл
        for block in blocks:
            output_file.write(hex(magma_decrypt(int(block, 16), key))[2:])
        print("Расшифрованный текст находится в файле output.txt")

# message = int(input(), 16)
# key = int(input(), 16)
# print(hex(magma_encrypt(message, key)))
# print(hex(magma_decrypt(magma_encrypt(message, key), key)))
