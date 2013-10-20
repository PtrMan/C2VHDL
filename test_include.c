
/*
void include_function(int a, int b, int c) {
	for(;;) {
	   int result = (a << 5) + (b >> 2);
   }

   return;
}*/

int abs(int value) {
   if( value < 0 ) {
      return -value;
   }
   return value;
}

void include_function()
{
   int a = -5;

   a = abs(a);

   report(a);

   a = -6;

   a = abs(a);

   report(a);
}
