# HeapSort para gem5 — adaptado do heapSort.txt (tutorial Venus → gem5)
# Compilar: riscv64-linux-gnu-gcc -static heapSort_100k.s -o heapSort.riscv

.section .rodata
fmt_int: .string "%d "
fmt_nl:  .string "\n"
msg_orig: .string "Array original (primeiros 20 ou menos):\n"
msg_sorted: .string "\nArray ordenado (decrescente, primeiros 20 ou menos):\n"
msg_skipped: .string "[Visualização pulada pois o array é muito grande]\n"

.data
n_elems: .word 100000  # Tamanho do array (100k elementos)
rand_state: .word 42   # Semente inicial para o gerador pseudo-aleatório (LCG)

.text
.globl main

# int rand_assembly()
# Implementação de um Linear Congruential Generator (LCG) simples:
# X_{n+1} = (1103515245 * X_n + 12345) & 0x7FFFFFFF
rand_assembly:
    la t0, rand_state
    lw t1, 0(t0)        # Carrega o estado atual (semente)
    li t2, 1103515245   # Multiplicador a
    mul t1, t1, t2      # seed * a
    li t3, 12345        # Carrega c em t3
    add t1, t1, t3      # seed * a + c
    sw t1, 0(t0)        # Salva o novo estado
    srli a0, t1, 16     # Desloca para obter bits de melhor qualidade
    li t3, 0x7FFF       # Carrega máscara em t3
    and a0, a0, t3      # Aplica a máscara
    ret

# void swap(int *a, int *b)
swap:
    lw t0, 0(a0)
    lw t1, 0(a1)
    sw t1, 0(a0)
    sw t0, 0(a1)
    ret

# void heapify(int *arr, int n, int i)
heapify:
    addi sp, sp, -32
    sd ra, 24(sp)
    sd s1, 16(sp)
    sd s2, 8(sp)
    sd s3, 0(sp)

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
    ld ra, 24(sp)
    ld s1, 16(sp)
    ld s2, 8(sp)
    ld s3, 0(sp)
    addi sp, sp, 32
    ret

# void heapSort(int *arr, int n)
heapSort:
    addi sp, sp, -40
    sd ra, 32(sp)
    sd s1, 24(sp)
    sd s2, 16(sp)
    sd s3, 8(sp)
    sd s4, 0(sp)

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
    ld ra, 32(sp)
    ld s1, 24(sp)
    ld s2, 16(sp)
    ld s3, 8(sp)
    ld s4, 0(sp)
    addi sp, sp, 40
    ret

# void imprimirArray(int *arr, int n)
imprimirArray:
    addi sp, sp, -24
    sd ra, 16(sp)
    sd s1, 8(sp)
    sd s2, 0(sp)

    mv s1, a0
    mv s2, a1
    
    li t0, 20
    bgt s2, t0, print_skip   # Se n > 20, pula a impressão
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
    j print_exit

print_skip:
    la a0, msg_skipped
    jal ra, printf

print_exit:
    ld ra, 16(sp)
    ld s1, 8(sp)
    ld s2, 0(sp)
    addi sp, sp, 24
    ret

.globl main
main:
    addi sp, sp, -32
    sd ra, 24(sp)
    sd s1, 16(sp)
    sd s2, 8(sp)
    sd s3, 0(sp)

    # Carrega n_elems
    la t0, n_elems
    lw s2, 0(t0)
    
    # Aloca memória dinamicamente via malloc: n_elems * 4 bytes
    slli a0, s2, 2
    jal ra, malloc
    mv s1, a0

    # Inicializa o array com valores aleatórios usando o LCG em assembly
    li s3, 0            # s3 é o contador do loop de preenchimento (índice = 0)
populate_loop:
    bge s3, s2, populate_done  # Se índice >= n_elems, termina
    jal ra, rand_assembly     # Gera um número aleatório em a0
    slli t0, s3, 2            # t0 = índice * 4
    add t1, s1, t0            # t1 = endereço de arr[índice]
    sw a0, 0(t1)              # Salva o valor aleatório no array
    addi s3, s3, 1            # índice++
    j populate_loop
populate_done:

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

    # Libera a memória alocada
    mv a0, s1
    jal ra, free

    ld ra, 24(sp)
    ld s1, 16(sp)
    ld s2, 8(sp)
    ld s3, 0(sp)
    addi sp, sp, 32
    ret
