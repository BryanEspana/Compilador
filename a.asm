# Compiscript:
# function main(): void {
#     let edad: integer = 18;
#     if (edad >= 18) print 1; else print 0;
# }

.data
  nl: .asciiz "\n"

.text
  .globl main
main:
  # edad = 18
  li   $t0, 18

  # if (edad >= 18)  <=>  !(edad < 18)
  # Usamos slti: $t1 = (t0 < 18) ? 1 : 0
  slti $t1, $t0, 18
  bne  $t1, $zero, ELSE     # si (edad < 18) -> ELSE

THEN:
  # print 1
  li   $a0, 1
  li   $v0, 1
  syscall
  j    ENDIF

ELSE:
  # print 0
  li   $a0, 0
  li   $v0, 1
  syscall

ENDIF:
  # salto de línea
  li   $v0, 4
  la   $a0, nl
  syscall

  # salir del programa
  li   $v0, 10
  syscall
