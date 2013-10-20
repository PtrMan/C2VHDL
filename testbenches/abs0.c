// PASS
// test for correct function of the
// * call to functions
// * combinatorial logic stuff

int abs(int value) {
   if (value < 0) {
      return -value;
   }
   return value;
}

void include_function()
{
   int a = -5;

   a = abs(a);

   assert(a == 5);

   a = 6;

   a = abs(a);

   assert(a == 6);
}
