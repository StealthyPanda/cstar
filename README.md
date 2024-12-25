# C*

An extention of C with useful constructs like union return types.

# Installation

Install python, then install using pip:

```bash
pip install git+https://github.com/StealthyPanda/cstar
```


# Usage

Use the CLI `cstar` to parse any `.cmp` file to C code.

Example:

`example.cmp`
```c
[int | void] returnIfEven(int x) {
    // return the number if even, else return false.
    if (x % 2) {
        return[void];
    } else {
        return[int] x;
    }
}


int main() {

    int input;
    printf("Enter a number: ");
    scanf("%d", &input);

    [ x = returnIfEven(input) ] {
        int { printf("The number %i is even!", x); }
        void { printf("The given number is not even!"); }
    }

    return 0;
}
```

Running `cstar example.cmp` outputs `example.c`, which can be run or used with the rest of your C codebase.


