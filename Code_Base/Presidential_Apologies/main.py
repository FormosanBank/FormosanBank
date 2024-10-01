import re

# file = open("../Sources/English/English Presidenial Apology.txt", "r")
# t  = file.read()
# print(len(t.split(".")))

# file = open("../Sources/Chinese/Traditional Chinese Presidential Apology.txt", "r")
# p  = file.read()
# p = p.split("。")
# # print(len(p.split("。")))
# print(len(p))
# print(p[98:])

# file = open("../Sources/English/test.txt", "r")
# t  = file.read()
# t = t.split('.')
# print(len(t))
# print(t[98:])
# for i in range(len(p)):
#     print(p[i], f" \n {i} ----------- \n")

file = open("../Sources/English/test2.txt", "r")
t  = file.read()
t = t.split('.')
t=t[:-1]
print(len(t))


file = open("../Sources/English/test3.txt", "r")
p  = file.read()
p = p.split('。')
p = p[:-1]
print(len(p))



for i in range(101):
    print(t[i], "\n", p[i])
    print(f"{i}\n--------------\n")

