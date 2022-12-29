
#include <string>
#include <cassert>
#include <cstdio>
#include <algorithm>

void copy(const std::string& source, char* dest, std::size_t len)
{
  const auto length = source.copy(dest, len);
  printf("copy(..., len=%d) = %d\n", len, length);
  dest[std::min(length,  len - 1)] = '\0';
}

int main()
{
  std::string source("hello world");
  const std::size_t length = 2;
  {
    char buffer[length];
    std::fill_n(buffer, length, 'a');
    copy(source, buffer, length);
    printf("%s\n", buffer);
  }

  return 0;
}
