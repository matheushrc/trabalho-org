.data
arr: .word 12, 11, 13, 5, 6, 7
msg_orig: .asciz "Array original:\n"
msg_sorted: .asciz "\nArray ordenado com Heap Sort (ordem decrescente):\n"
space: .asciz " "
newline: .asciz "\n"

.text
.globl main

# ------------------------------------------------------------
# swap(int *a, int *b)
# ------------------------------------------------------------
swap:
    lw t0, 0(a0)              # t0 = *a
    lw t1, 0(a1)              # t1 = *b
    sw t1, 0(a0)              # *a = t1
    sw t0, 0(a1)              # *b = t0
    ret                       # retorna

# ------------------------------------------------------------
# heapify(int *arr, int n, int i)
# ------------------------------------------------------------
heapify:
    addi sp, sp, -16          # cria frame na stack
    sw ra, 12(sp)             # salva ra
    sw s1, 8(sp)              # salva s1
    sw s2, 4(sp)              # salva s2
    sw s3, 0(sp)              # salva s3

    mv s1, a0                 # s1 = arr
    mv s2, a1                 # s2 = n

    mv s3, a2                 # s3 = menor = i

    slli t1, a2, 1            # t1 = 2*i
    addi t1, t1, 1            # t1 = esquerda = 2*i + 1

    slli t2, a2, 1            # t2 = 2*i
    addi t2, t2, 2            # t2 = direita = 2*i + 2

    blt t1, s2, check_left    # se esquerda < n, verifica filho esquerdo
    j check_right             # caso contrario, pula

check_left:
    slli t3, t1, 2            # offset = esquerda * 4
    add t3, s1, t3            # endereco de arr[esquerda]
    lw t4, 0(t3)              # t4 = arr[esquerda]

    slli t5, s3, 2            # offset = menor * 4
    add t5, s1, t5            # endereco de arr[menor]
    lw t6, 0(t5)              # t6 = arr[menor]

    blt t4, t6, set_left_min  # se arr[esquerda] < arr[menor], atualiza
    j check_right             # senao, segue

set_left_min:
    mv s3, t1                 # menor = esquerda

check_right:
    blt t2, s2, do_check_right # se direita < n, verifica filho direito
    j check_swap               # caso contrario, pula

do_check_right:
    slli t3, t2, 2            # offset = direita * 4
    add t3, s1, t3            # endereco de arr[direita]
    lw t4, 0(t3)              # t4 = arr[direita]

    slli t5, s3, 2            # offset = menor * 4
    add t5, s1, t5            # endereco de arr[menor]
    lw t6, 0(t5)              # t6 = arr[menor]

    blt t4, t6, set_right_min # se arr[direita] < arr[menor], atualiza
    j check_swap               # senao, segue

set_right_min:
    mv s3, t2                 # menor = direita

check_swap:
    beq s3, a2, done_heapify   # se menor == i, heap ok

    slli t3, a2, 2            # offset i * 4
    add t3, s1, t3            # &arr[i]
    slli t4, s3, 2            # offset menor * 4
    add t4, s1, t4            # &arr[menor]

    mv a0, t3                 # a0 = &arr[i]
    mv a1, t4                 # a1 = &arr[menor]
    jal ra, swap              # chama swap

    mv a0, s1                 # a0 = arr
    mv a1, s2                 # a1 = n
    mv a2, s3                 # a2 = menor
    jal ra, heapify           # chamada recursiva


done_heapify:
    lw ra, 12(sp)             # restaura ra
    lw s1, 8(sp)              # restaura s1
    lw s2, 4(sp)              # restaura s2
    lw s3, 0(sp)              # restaura s3
    addi sp, sp, 16           # libera frame
    ret                       # retorna

# ------------------------------------------------------------
# heapSort(int *arr, int n)
# ------------------------------------------------------------
heapSort:
    addi sp, sp, -20          # cria frame
    sw ra, 16(sp)             # salva ra
    sw s1, 12(sp)             # salva s1
    sw s2, 8(sp)              # salva s2
    sw s3, 4(sp)              # salva s3
    sw s4, 0(sp)              # salva s4

    mv s1, a0                 # s1 = arr
    mv s2, a1                 # s2 = n

    srli s3, s2, 1            # s3 = n/2
    addi s3, s3, -1           # s3 = s3 - 1

build_loop:
    blt s3, x0, build_done    # se i < 0, termina
    mv a0, s1                 # a0 = arr
    mv a1, s2                 # a1 = n
    mv a2, s3                 # a2 = i
    jal heapify               # heapify(arr, n, i)
    addi s3, s3, -1           # i--
    j build_loop              # repete

build_done:
    addi s4, s2, -1           # s4 = i = n-1

extract_loop:
    ble s4, x0, extract_done  # se i <= 0, termina
    slli t2, x0, 2            # offset de 0
    add t2, s1, t2            # &arr[0]
    slli t3, s4, 2            # offset i * 4
    add t3, s1, t3            # &arr[i]

    mv a0, t2                 # a0 = &arr[0]
    mv a1, t3                 # a1 = &arr[i]
    jal ra, swap              # swap(&arr[0], &arr[i])

    mv a0, s1                 # a0 = arr
    mv a1, s4                 # a1 = i
    li a2, 0                  # a2 = 0
    jal ra, heapify           # heapify(arr, i, 0)

    addi s4, s4, -1           # i--
    j extract_loop            # repete

extract_done:
    lw ra, 16(sp)             # restaura ra
    lw s1, 12(sp)             # restaura s1
    lw s2, 8(sp)              # restaura s2
    lw s3, 4(sp)              # restaura s3
    lw s4, 0(sp)              # restaura s4
    addi sp, sp, 20           # libera frame
    ret                       # retorna

# ------------------------------------------------------------
# imprimirArray(int *arr, int n)
# ------------------------------------------------------------
imprimirArray:
    addi sp, sp, -12          # cria frame
    sw ra, 8(sp)              # salva ra
    sw s1, 4(sp)              # salva s1
    sw s2, 0(sp)              # salva s2

    mv s1, a0                 # s1 = arr
    mv s2, a1                 # s2 = n
    li t0, 0                  # i = 0

print_loop:
    bge t0, s2, print_done    # se i >= n, termina
    slli t1, t0, 2            # offset i * 4
    add t1, s1, t1            # &arr[i]
    lw a1, 0(t1)              # a1 = arr[i]
    li a0, 1                  # ecall 1: print_int
    ecall                     # imprime inteiro

    la a1, space              # a1 = " "
    li a0, 4                  # ecall 4: print_string
    ecall                     # imprime espaco

    addi t0, t0, 1            # i++
    j print_loop              # repete

print_done:
    la a1, newline            # a1 = "\n"
    li a0, 4                  # ecall 4: print_string
    ecall                     # imprime quebra de linha

    lw ra, 8(sp)              # restaura ra
    lw s1, 4(sp)              # restaura s1
    lw s2, 0(sp)              # restaura s2
    addi sp, sp, 12           # libera frame
    ret                       # retorna

# ------------------------------------------------------------
# main
# ------------------------------------------------------------
main:
    li s2, 6                  # n = 6
    la s1, arr                # s1 = arr

    la a1, msg_orig           # a1 = "Array original:\n"
    li a0, 4                  # ecall 4: print_string
    ecall                     # imprime mensagem

    mv a0, s1                 # a0 = arr
    mv a1, s2                 # a1 = n
    jal ra, imprimirArray     # imprime array

    mv a0, s1                 # a0 = arr
    mv a1, s2                 # a1 = n
    jal heapSort              # ordena

    la a1, msg_sorted         # a1 = "Array ordenado..."
    li a0, 4                  # ecall 4: print_string
    ecall                     # imprime mensagem

    mv a0, s1                 # a0 = arr
    mv a1, s2                 # a1 = n
    jal ra, imprimirArray     # imprime array ordenado

    li a0, 10
    ecall
