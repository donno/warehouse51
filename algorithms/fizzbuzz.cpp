// Implement the game of Fizz-Buzz.
//
// This game is typically played by children at school to test their division
// skill. They sit in a circle if a player makes a mistake they are eliminated
// and the winner is the final player left in.

#include <array>
#include <utility>

#include <stdio.h>

// This constant defines what number the game ends before.
constexpr auto last_number = 1024;

constexpr const char *const fizz = "Fizz";
constexpr const char *const buzz = "Buzz";
constexpr const char *const fizz_buzz = "FizzBuzz";

#ifndef FIZZBUZZ_HARDCODED_CACHE
namespace details
{
template <typename INTEGER> static constexpr const char *const string_from_value(INTEGER value) noexcept
{
    if (value % 15 == 0)
    {
        return fizz_buzz;
    }
    if (value % 3 == 0)
    {
        return fizz;
    }
    if (value % 5 == 0)
    {
        return buzz;
    }
    return nullptr;
}

template <std::size_t... I>
static constexpr std::array<const char *, sizeof...(I)> build_cache(std::integer_sequence<std::size_t, I...>) noexcept
{
    return std::array<const char *, sizeof...(I)>{string_from_value(I + 1)...};
}

static constexpr auto build_cache() noexcept
{
    return build_cache(std::make_index_sequence<15>{});
}
} // namespace details

constexpr auto cache = details::build_cache();

#else

const char *const cache[] = {
    nullptr, nullptr, fizz,    nullptr, buzz,    fizz,    nullptr,   nullptr,
    fizz,    buzz,    nullptr, fizz,    nullptr, nullptr, fizz_buzz,
};
#endif

void fizz_buzz_traditional();
void fizz_buzz_with_cache();

// A traditional implementation of Fizz-Buzz game.
void fizz_buzz_traditional()
{
    for (int i = 1; i < last_number + 1; ++i)
    {
        if (i % 15 == 0)
        {
            puts(fizz_buzz);
        }
        else if (i % 3 == 0)
        {
            puts(fizz);
        }
        else if (i % 5 == 0)
        {
            puts(buzz);
        }
        else
        {
            printf("%d\n", i);
        }
    }
}

// A implementation of Fizz-Buzz game where the sequence is cached.
void fizz_buzz_with_cache()
{
    constexpr auto modulus = std::size(cache);
    static_assert(modulus == 15);
    for (int i = 0; i < last_number; ++i)
    {
        const auto output = cache[i % modulus];
        if (output)
        {
            puts(output);
        }
        else
        {
            printf("%d\n", i + 1);
        }
    }
}

int main()
{
    // fizz_buzz_traditional();
    fizz_buzz_with_cache();

    return 0;
}
