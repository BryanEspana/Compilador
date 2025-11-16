.data
    .align 2
newline: .asciiz "\n"


.text
    .globl main


main:
    li $v0, 10  # syscall exit
    syscall