# Do Venus para o Gem5

Neste tutorial, vamos pegar um código elaborado no Venus e portá-lo no gem5. O código assembly elaborado no Venus não funciona diretamente no gem5 e exige as seguintes correções de sintaxe e estrutura. Para isso, faça download do arquivo base no link:

> https://github.com/RicardoParizotto/Tutorial_venus_to_gem5/blob/main/venus.s

Considere que o seguinte recebe um vetor de char, que é geralmente configurado pelo usuário na interface do Venus. Esse valor é copiado para uma variável alocada dinamicamente, e os valores são mostrados na tela. Nosso trabalho será fazer modificações no código base para que o gem5 suporte o nosso código.

---

## Passo 1: Arrumar a Sintaxe

O Venus permite expressar instruções sem separação por vírgulas. Porém, como vamos usar as ferramentas do GCC, será necessário adicionar vírgulas em todas as instruções do código.

**Antes:**

```asm
addi a0 zero 1
mv a1 t4
```

**Depois:**

```asm
addi a0, zero, 1
mv a1, t4
```

---

## Passo 2: Retorno de Função

Geralmente fazíamos programas que não tinham uma função "global", ou que tinha, mas nem sempre retornava um valor. Para executar corretamente nosso código no gem5, temos que preservar e restaurar `ra` na `main`. Garanta que existe uma função `main`, e adicione as seguintes instruções:

**No início da `main`:**

```asm
addi sp, sp, -4
sw ra, 0(sp)
```

**Por fim, antes de retornar:**

```asm
lw ra, 0(sp)
addi sp, sp, 4
```

---

## Passo 3: Adicionar Retorno de Função

Na função `main`, use a instrução `ret` para retornar corretamente após a execução do código.

---

## Passo 4: Eliminação de Endereços de Memória Estática

Em gem5, usar endereços de memória fixos (como `0x0FFFFFE8` do Venus) pode gerar um **Segmentation Fault** por pertencerem ao espaço protegido do sistema operacional emulado.

### 4.1 Solução: Usar a diretiva `.data`

Use a diretiva de assembler `.data` para definir uma seção de dados estruturada. O montador se encarregará de posicionar as variáveis em uma região segura da memória durante a linkagem do binário.

```asm
.data
my_vector: .word 10, 20, 30, 40, 50
```

Na seção `.text`, use a instrução `la` (Load Address) para carregar o endereço da memória alocada:

```asm
.text
.globl main

...

main:
    ...
    la s1, my_vector
```

---

## Passo 5: Substituição das Chamadas de Sistema (Uso da Libc)

Ao invés de programar diretamente via Assembly a chamada bruta ao kernel emulado do gem5, aproveite que a toolchain do GCC fornece suporte à biblioteca C. Substitua as syscalls proprietárias do Venus por chamadas simplificadas a `malloc` e `printf`.

**Exemplo — `malloc(20)` para 5 ints de 4 bytes:**

```asm
li a0, 20
call malloc
```

Para mostrar o inteiro, configure uma seção somente leitura para armazenar a string de formato para `printf`:

```asm
.section .rodata
fmt: .string "%d\n"
```

**Substituição da syscall de print:**

| Versão no Venus    | Versão no gem5 |
| ------------------ | -------------- |
| `addi a0, zero, 1` | `la a0, fmt`   |
| `mv a1, t4`        | `mv a1, t4`    |
| `ecall`            | `call printf`  |

> **Atenção:** As variáveis temporárias `t0…tn` **não são preservadas** internamente por `printf` e `malloc`. Por isso, substitua-as por registradores do tipo `s`:

| Registrador Original (Temporário) | Novo Registrador Substituto (Salvo) |
| --------------------------------- | ----------------------------------- |
| `t0`                              | `s3`                                |
| `t1`                              | `s4`                                |
| `t3`                              | `s5`                                |

---

## Configurando o Ambiente e Rodando o Código RISC-V

### Repositório base

```bash
git clone git@github.com:RicardoParizotto/Trabalho_org_gem5.git
```

Esse repositório possui modelos para gem5 de CPUs simples que poderão servir de ponto inicial para o trabalho.

### Compilar o Código Assembly

Use o `riscv64-linux-gnu-gcc` para compilar o arquivo assembly em um binário RISC-V estático:

```bash
riscv64-linux-gnu-gcc -static solucao.s -o solucao.riscv
```

### Simular no gem5

Execute o binário compilado usando o simulador `gem5.opt`, especificando o modelo de simulação e o caminho para o binário:

```bash
./gem5/build/RISCV/gem5.opt models/simple-riscv.py --binary programs/solucao.riscv
```
