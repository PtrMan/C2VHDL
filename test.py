#!/usr/bin/env python
import os
import sys

os.system("python-coverage erase")

def test(test, code):
  f = open("test.c", 'w')
  f.write(code)
  f.close()
  result = os.system("python-coverage run -p c2vhdl.py iverilog run test.c")
  if result == 0:
    print test, "...pass"
  else:
    print test, "...fail"
    sys.exit(0)

def test_fails(test, code):
  f = open("test.c", 'w')
  f.write(code)
  f.close()
  print "One error expected ..."
  result = os.system("python-coverage run -p c2vhdl.py iverilog run test.c")
  if result == 0:
    print test, "...fail"
    sys.exit(0)
  else:
    print test, "...pass"

test("struct 1",
"""
struct blah {int a; int b; int c;};
int main(){
  struct blah myblah;
  myblah.a = 1;
  myblah.b = 2;
  myblah.c = 3;
  assert(myblah.a == 1);
  assert(myblah.b == 2);
  assert(myblah.c == 3);
  return 0;
}
"""
)
test("struct 2",
"""
struct as {int a; int b; int c;};
int main(){
  struct as asa;
  struct as asb;
  asa.a = 1;
  asb.a = 3;
  asa.b = 2;
  asb.b = 2;
  asa.c = 3;
  asb.c = 1;
  assert(asa.a == 1);
  assert(asb.a == 3);
  assert(asa.b == 2);
  assert(asb.b == 2);
  assert(asa.c == 3);
  assert(asb.c == 1);
  return 0;
}
"""
)
test("struct 3",
"""
typedef struct {int a; int b; int c;} blah;
int main(){
  blah myblah;
  myblah.a = 1;
  myblah.b = 2;
  myblah.c = 3;
  assert(myblah.a == 1);
  assert(myblah.b == 2);
  assert(myblah.c == 3);
  return 0;
}
"""
)
test("struct 4",
"""
typedef struct{int a; int b; int c;} mytype;
typedef struct{mytype a;} othertype;
int main(){
  othertype a;
  othertype b;
  a.a.a = 1;
  b.a.a = 2;
  a.a.b = 3;
  b.a.b = 4;
  a.a.c = 5;
  b.a.c = 6;
  assert(a.a.a == 1);
  assert(b.a.a == 2);
  assert(a.a.b == 3);
  assert(b.a.b == 4);
  assert(a.a.c == 5);
  assert(b.a.c == 6);
  return 0;
}
"""
)
test("include 1",
"""#include "test_include.c"
int main(){
  assert(include_function()==12);
  return 0;
}
"""
)
test("switch 1",
     """int main(){
        switch(0){
            case 0: return 3;
            case 1: return 2;
            case 2: return 1;
            default: return 0;
        }
     }
     """
)
test("switch 2",
     """int main(){
        switch(2){
            case 0: return 3;
            case 1: return 2;
            case 2: return 1;
            default: return 0;
        }
     }
     """
)
test("switch 3",
     """int main(){
        switch(5){
            case 0: return 3;
            case 1: return 2;
            case 2: return 1;
            default: return 0;
        }
     }
     """
)
test("switch 4",
     """int main(){
        int a = 0;
        switch(0){
            case 0: a = 1;
            case 1: a = 2;
            case 2: a = 3;
            default: a = 4;
        }
        return a;
     }
     """
)
test("switch 5",
     """int main(){
        int a = 0;
        switch(1){
            case 0: a = 1;
            case 1: a = 2;
            case 2: a = 3;
            default: a = 4;
        }
        return a;
     }
     """
)
test("switch 6",
     """int main(){
        int a = 1;
        switch(10){
            case 0: a = 1;
            case 1: a = 2;
            case 2: a = 3;
            default: a = 4;
        }
        return a;
     }
     """
)
test("switch 7",
     """int main(){
        int a = 1;
        switch(0){
            case 0: a = 1; break;
            case 1: a = 2; break;
            case 2: a = 3; break;
            default: a = 4; break;
        }
        return a;
     }
     """
)
test("switch 8",
     """int main(){
        int a = 1;
        switch(2){
            case 0: a = 1; break;
            case 1: a = 2; break;
            case 2: a = 3; break;
            default: a = 4; break;
        }
        return a;
     }
     """
)
test("switch 9",
"""int main(){
int a = 1;
switch(9){
    case 0: a = 1; break;
    case 1: a = 2; break;
    case 2: a = 3; break;
    default: a = 4; break;
}
return a;
}
"""
)

test("break 0",
"""
int main(){
  int a;
  while(1){
    break;
    assert(0);
  }
  return 0;
}
""")
test("break 1",
"""
int main(){
  int a;
  for(a=0; a<20; a++){
    if(a == 10){
      break;
    }
  }
  assert(a == 10);
  return 0;
}
""")
test("continue 0",
"""
int main(){
  int a;
  for(a=1; a<=10; a++){
    if(a <= 5){
      continue; 
    } 
    assert(a > 5);
  }
  return 0;
}
""")
test("ternary 0",
"""
int main(){
  int a;
  int b=2;
  int c=3;
  assert((1?2:3) == 2);
  assert((0?2:3) == 3);
  a = 1;
  assert((a?b:c) == 2);
  a = 0;
  assert((a?b:c) == 3);
  assert((1?b:c) == 2);
  assert((0?b:c) == 3);
  return 0;
}
""")
test("inplace 0",
"""
int main(){
  int a = 1;
  a += 1;
  assert(a == 2);
  a -= 1;
  assert(a == 1);
  a *= 2;
  assert(a == 2);
  a /= 2;
  assert(a == 1);
  a |= 2;
  assert(a == 3);
  a &= 2;
  assert(a == 2);
  a <<= 1;
  assert(a == 4);
  a >>= 1;
  assert(a == 2);
  return 0;
}
""")
test("inplace 1",
"""
int main(){
  int a[100];
  a[0] = 1;
  a[20] = 1;
  a[20] += 1;
  assert(a[20] == 2);
  a[20] -= 1;
  assert(a[20] == 1);
  a[20] *= 2;
  assert(a[20] == 2);
  a[20] /= 2;
  assert(a[20] == 1);
  a[20] |= 2;
  assert(a[20] == 3);
  a[20] &= 2;
  assert(a[20] == 2);
  a[20] <<= 1;
  assert(a[20] == 4);
  a[20] >>= 1;
  assert(a[20] == 2);
  assert(a[0] == 1);
  return 0;
}
""")
test("increment",
"""
int main(){
  int a = 1;
  a++;
  assert(a == 2);
  a--;
  assert(a == 1);
  return 0;
}

""")

test("assert 0",
"""int main(){
  assert(1);
  return 0;
}
""")
test_fails("assert 1",
"""int main(){
  assert(0);
  return 0;
}
""")
test("assign",
"""int main(){
  int a;
  int b;
  int c;
  a = 10;
  b = 20;
  c = a + b;
  assert(a == 10);
  assert(b == 20);
  assert(c == 30);
  return 0;
}
""")
test("while",
"""int main(){
  int a = 10;
  int b = 0;
  while(a){
    a = a - 1;
    b = b + 1;
  }
  assert(b == 10);
  return 0;
}
""")
test("while 1",
"""int main(){
  int a = 0;
  while(1){
    a = a + 1;
    if(a == 10){
      return 0;
    }
  }
}
""")
test("while 2",
"""int main(){
  while(0){
    assert(0);
  }
  return 0;
}
""")
test("if",
"""int main(){
  int a = 0;
  int b = 0;
  if(a){
    b = 10;
    assert(0);
  } else {
    b = 20;
  }
  assert(b == 20);
  return 0;
}
""")
test("if 1",
"""int main(){
  int a = 1;
  int b = 0;
  if(a){
    b = 10;
  } else {
    b = 20;
    assert(0);
  }
  assert(b == 10);
  return 0;
}
""")
test("if 2",
"""int main(){
  int b = 0;
  if(0){
    b = 10;
    assert(0);
  } else {
    b = 20;
  }
  assert(b == 20);
  return 0;
}
""")
test("if 3",
"""int main(){
  int b = 0;
  if(1){
    b = 10;
  } else {
    b = 20;
    assert(0);
  }
  assert(b == 10);
  return 0;
}
""")
test("if 4",
"""int main(){
  int b = 0;
  if(0){
    b = 10;
    assert(0);
  }
  assert(b == 0);
  return 0;
}
""")
test("for 0",
"""int main(){
  int a = 0;
  int b;
  int c = 1;
  for(a=0; a<10; a++){
   b = b + 1;
   c = c + 1;
  }
  assert(b == 10);
  assert(c == 11);
  return 0;
}
""")
test("for 1",
"""int main(){
  int a = 0;
  int b;
  int c = 1;
  for(; a<10; a++){
   b = b + 1;
   c = c + 1;
  }
  assert(b == 10);
  assert(c == 11);
  return 0;
}
""")
test("for 2",
"""int main(){
  int a = 0;
  int b;
  int c = 1;
  for(;a<10;){
   b = b + 1;
   c = c + 1;
   a++;
  }
  assert(b == 10);
  assert(c == 11);
  return 0;
}
""")
test("for 3",
"""int main(){
  int a = 0;
  int b;
  int c = 1;
  for(;;){
   if(a>=10) break;
   b = b + 1;
   c = c + 1;
   a++;
  }
  assert(b == 10);
  assert(c == 11);
  return 0;
}
""")
test("number 0",
"""int main(){
  return 1;
}
""")
test("report 0",
"""int main(){
  int a = 0;
  int b = 1;
  int c = 2;
  report(a);
  report(b);
  report(c);
  return 0;
}
""")
test("declare 0",
"""int main(){
  int a = 10;
  int b = 20, c = 30;
  int d[100], e[200];
  assert(a==10);
  assert(b==20);
  assert(c==30);
  return 0;
}
""")
test("wait_clocks 0",
"""int main(){
  int a = 10;
  wait_clocks(a);
  wait_clocks(10);
  return 0;
}
""")
test("function",
"""

int func(int a){
  return a + 10;
}

int main(){
  int a = func(10);
  assert(a == 20);
  return 0;
}

""")
test("function 1",
"""

int func(int a){
  assert(a == 20);
  return 0;
}

int main(){
  func(20);
  return 0;
}

""")

test("function 2",
"""

int func(int a, int b, int c){
  return a;
}

int main(){
  assert(func(1, 2, 3) == 1);
  return 0;
}

""")

test("function 3",
"""

int func(int a, int b, int c){
  return b;
}

int main(){
  assert(func(1, 2, 3) == 2);
  return 0;
}

""")

test("function 4",
"""

int func(int a, int b, int c){
  return c;
}

int main(){
  assert(func(1, 2, 3) == 3);
  return 0;
}

""")

test("function 5",
"""

int another(int a){
  return a + 1;
}

int func(int a){
  return another(a) + 1;
}

int main(){
  assert(func(0) == 2);
  return 0;
}

""")

test_fails("function 6",
"""

int func(int a, int b){
  return b;
}

int main(){
  assert(func(1, 2, 3) == 3);
  return 0;
}

""")
test("expression 1",
"""
int main(){
  int a = 1;
  int b = 2;
  int c = 3;
  assert(a + b + c == 6);
  return 0;
}

""")
test("expression 2",
"""
int main(){
  int a = 1;
  int b = 2;
  int c = 3;
  assert(a - b - c == -4);
  return 0;
}

""")
test("expression 3",
"""
int main(){
  int a = 1;
  int b = 2;
  int c = 3;
  assert(a - (b - c) == 2);
  return 0;
}

""")
test("expression 4",
"""
int main(){
  int a = 1;
  int b = 2;
  int c = 3;
  assert(a * b * c == 6);
  return 0;
}

""")
test("expression 5",
"""
int main(){
  int a = 1;
  int b = 2;
  int c = 3;
  assert(a/b/c == 0);
  return 0;
}

""")
test("expression 6",
"""
int main(){
  int a = 1;
  int b = 2;
  int c = 3;
  assert(a%b%c == 1);
  return 0;
}

""")
test("expression 7",
"""
int main(){
  int a = 1;
  int b = 2;
  int c = 3;
  assert(-a - (b - c) == 0);
  return 0;
}

""")
test("expression 8",
"""
int fail(){
  assert(0);
  return 0;
}
int main(){
  int a = 0 && fail();
  return 0;
}

""")
test("expression 9",
"""
int fail(){
  assert(0);
  return 0;
}
int main(){
  int a = 1 || fail();
  return 0;
}

""")
test("expression 10",
"""
int main(){
  int a = 1;
  assert(a << 2 == 4);
  return 0;
}

""")
test("expression 11",
"""
int main(){
  int a = 1;
  int b = 2;
  assert(a << b == 4);
  return 0;
}

""")
test("expression 12",
"""
int main(){
  int a = 4;
  assert(a >> 2 == 1);
  return 0;
}

""")
test("expression 13",
"""
int main(){
  int a = 4;
  int b = 2;
  assert(a >> b == 1);
  return 0;
}

""")
test("expression 14",
"""
int main(){
  int a = -1;
  assert(~a == 0);
  return 0;
}

""")
test("expression 15",
"""
int main(){
  int a = 1;
  assert(!a == 0);
  int a = 0;
  assert(!a == 1);
  return 0;
}

""")
test("expression 16",
"""
int main(){
  int a = 0xA;
  int b = 0x5;
  assert((a | b) == 0xF);
  assert((a ^ b) == 0xf);
  assert((a & b) == 0);
  return 0;
}

""")
test("expression 17",
"""
int fail(){
  assert(0);
  return 0;
}
int main(){
  int b = 0;
  int a = b && fail();
  return 0;
}

""")
test("expression 18",
"""
int fail(){
  assert(0);
  return 0;
}
int main(){
  assert(~1);
  return 0;
}

""")
test("expression 19",
"""
int main(){
  assert(-1 < 1);
  assert(-1 < 0);
  assert(0 <= 0);
  assert(0 >= 0);
  assert(1 >= 0);
  assert(1 >= -1);
  assert(1 > -1);
  assert(1 > 0);
  assert(12 != 13);
  assert(100 == 100);
  return 0;
}

""")
test("comment 0",
"""
int main(){
  //assert(0);
  //assert(0);
  //assert(0);
  return 0;
}

""")
test("comment 1",
"""
int main(){
  /*assert(0);
  assert(0);
  assert(0);*/
  return 0;
}

""")
test("array 0",
"""
int main(){
  int a [1024];
  int b [1024];
  a[0] = 1;
  a[1] = 2;
  a[3] = 3;
  assert(a[0] == 1);
  assert(a[1] == 2);
  assert(a[3] == 3);
  return 0;
}

""")

test("array 1",
"""
int main(){
  int a [1024];
  int b [1024];
  a[0] = 10;
  b[0] = 20;
  a[1] = 30;
  b[1] = 40;
  a[3] = 50;
  b[3] = 60;
  assert(a[0] == 10);
  assert(b[0] == 20);
  assert(a[1] == 30);
  assert(b[1] == 40);
  assert(a[3] == 50);
  assert(b[3] == 60);
  return 0;
}

""")

test_fails("error 0",
"""
int main(){
  int a;
  a = c;
  return 0;
}

""")

test_fails("error 1",
"""
int main(){
  int a;
}

""")

test_fails("error 2",
"""
int main(){
  int a blah;
}

""")

test_fails("error 3",
"""
int main(){
  int a;
  b = a;
}

""")

test_fails("error 4",
"""
int main(){
  int a;
  a = c();
}

""")

test_fails("error 5",
"""
int main(){
  int a;
  a==;
}

""")
test_fails("error 6",
"""
int main(){
  int a;
  a=00x;
}

""")
test_fails("error 7",
"""
int main(){
  switch(1){
    case 0:
    default:
    default:
  }
  return 0;
}
""")
test_fails("error 8",
"""
int main(){
  default:
  return 0;
}
""")
test_fails("error 9",
"""
int main(){
  case 1:
  return 0;
}
""")
test_fails("error 10",
"""
int main(){
  int a = 12;
  switch(a){
    case a + 1:
    a++;
  }
  return 0;
}
""")
test_fails("error 11",
"""
int myfunction(){
  return 0;
}
int main(){
  int a = 12;
  myfunction()=10;
  return 0;
}
""")
test("input 1",
"""
int main(){
  int b;
  b = input_a();
  return 0;
}

""")

test("output 1",
"""
int main(){
   output_a(12);
  return 0;
}

""")

test("input output 1",
"""
int main(){
  if (input_select()){
    output_z(input_a());
  } else {
    output_z(input_b());
  }
  return 0;
}

""")

test("input output 2",
"""
int arbiter(){
  while(1){
    if(ready_a()) output_z(input_a());
    if(ready_b()) output_z(input_b());
  }
  return 0;
}

""")

test("main not main",
"""
int main(){
  assert(0);
  return 0;
}

//last function is always main
int real_main(){
  return 0;
}
""")

os.system("python-coverage run -p c2vhdl.py")
os.system("python-coverage combine")
os.system("python-coverage report")
os.system("python-coverage annotate c2vhdl.py")
