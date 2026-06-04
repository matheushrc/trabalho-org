# HeapSort para gem5 — adaptado do heapSort.txt (tutorial Venus → gem5)
# Compilar: riscv64-linux-gnu-gcc -static heapSort_gem5.s -o heapSort.riscv

.section .rodata
fmt_int: .string "%d "
fmt_nl:  .string "\n"
msg_orig: .string "Array original:\n"
msg_sorted: .string "\nArray ordenado (decrescente):\n"

.data
arr_static: .word 12, 11, 13, 5, 6, 7
n_elems: .word 6

.text
.globl main

# void swap(int *a, int *b)
swap:
    lw t0, 0(a0)
    lw t1, 0(a1)
    sw t1, 0(a0)
    sw t0, 0(a1)
    ret

# void heapify(int *arr, int n, int i)
heapify:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s1, 8(sp)
    sw s2, 4(sp)
    sw s3, 0(sp)

    mv s1, a0
    mv s2, a1
    mv s3, a2

    slli t1, a2, 1
    addi t1, t1, 1

    slli t2, a2, 1
    addi t2, t2, 2

    blt t1, s2, check_left
    j check_right

check_left:
    slli t3, t1, 2
    add t3, s1, t3
    lw t4, 0(t3)

    slli t5, s3, 2
    add t5, s1, t5
    lw t6, 0(t5)

    blt t4, t6, set_left_min
    j check_right

set_left_min:
    mv s3, t1

check_right:
    blt t2, s2, do_check_right
    j check_swap

do_check_right:
    slli t3, t2, 2
    add t3, s1, t3
    lw t4, 0(t3)

    slli t5, s3, 2
    add t5, s1, t5
    lw t6, 0(t5)

    blt t4, t6, set_right_min
    j check_swap

set_right_min:
    mv s3, t2

check_swap:
    beq s3, a2, done_heapify

    slli t3, a2, 2
    add t3, s1, t3
    slli t4, s3, 2
    add t4, s1, t4

    mv a0, t3
    mv a1, t4
    jal ra, swap

    mv a0, s1
    mv a1, s2
    mv a2, s3
    jal ra, heapify

done_heapify:
    lw ra, 12(sp)
    lw s1, 8(sp)
    lw s2, 4(sp)
    lw s3, 0(sp)
    addi sp, sp, 16
    ret

# void heapSort(int *arr, int n)
heapSort:
    addi sp, sp, -20
    sw ra, 16(sp)
    sw s1, 12(sp)
    sw s2, 8(sp)
    sw s3, 4(sp)
    sw s4, 0(sp)

    mv s1, a0
    mv s2, a1

    srli s3, s2, 1
    addi s3, s3, -1

build_loop:
    blt s3, zero, build_done
    mv a0, s1
    mv a1, s2
    mv a2, s3
    jal ra, heapify
    addi s3, s3, -1
    j build_loop

build_done:
    addi s4, s2, -1

extract_loop:
    ble s4, zero, extract_done
    slli t2, zero, 2
    add t2, s1, t2
    slli t3, s4, 2
    add t3, s1, t3

    mv a0, t2
    mv a1, t3
    jal ra, swap

    mv a0, s1
    mv a1, s4
    li a2, 0
    jal ra, heapify

    addi s4, s4, -1
    j extract_loop

extract_done:
    lw ra, 16(sp)
    lw s1, 12(sp)
    lw s2, 8(sp)
    lw s3, 4(sp)
    lw s4, 0(sp)
    addi sp, sp, 20
    ret

# void imprimirArray(int *arr, int n)
imprimirArray:
    addi sp, sp, -12
    sw ra, 8(sp)
    sw s1, 4(sp)
    sw s2, 0(sp)

    mv s1, a0
    mv s2, a1
    li t0, 0

print_loop:
    bge t0, s2, print_done
    slli t1, t0, 2
    add t1, s1, t1
    lw a1, 0(t1)
    la a0, fmt_int
    jal ra, printf
    addi t0, t0, 1
    j print_loop

print_done:
    la a0, fmt_nl
    jal ra, printf

    lw ra, 8(sp)
    lw s1, 4(sp)
    lw s2, 0(sp)
    addi sp, sp, 12
    ret

# Copia n words de src para dst (alocação dinâmica simulada via malloc no main)
copiar_vetor:
    mv t0, a0
    mv t1, a1
    mv t2, a2
    li t3, 0
copy_loop:
    bge t3, t2, copy_done
    slli t4, t3, 2
    add t5, t0, t4
    lw t6, 0(t5)
    add t5, t1, t4
    sw t6, 0(t5)
    addi t3, t3, 1
    j copy_loop
copy_done:
    ret

.globl main
main:
    addi sp, sp, -4
    sw ra, 0(sp)

    la t0, n_elems
    lw s2, 0(t0)
    slli a0, s2, 2
    jal ra, malloc
    mv s1, a0

    la a0, arr_static
    mv a1, s1
    mv a2, s2
    jal ra, copiar_vetor

    la a0, msg_orig
    jal ra, printf

    mv a0, s1
    mv a1, s2
    jal ra, imprimirArray

    mv a0, s1
    mv a1, s2
    jal ra, heapSort

    la a0, msg_sorted
    jal ra, printf

    mv a0, s1
    mv a1, s2
    jal ra, imprimirArray

    lw ra, 0(sp)
    addi sp, sp, 4
    ret
