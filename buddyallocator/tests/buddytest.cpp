#include "CppUnitTest.h"

#include "../buddy.hpp"
#include "../buddy.cpp"

using namespace Microsoft::VisualStudio::CppUnitTestFramework;

constexpr std::size_t operator "" _st(unsigned long long n)
{
  return n;
}

namespace tests
{		
	TEST_CLASS(BuddyTests)
	{
	public:
		
		TEST_METHOD(DefaultConstructor)
		{
            donno::Buddy buddy;
            Assert::AreEqual(buddy.AvailableFreeSpace(), 1024_st);
		}

          TEST_METHOD(AllocateMoreThanDefaultSpace)
          {
            donno::Buddy buddy;
            Assert::AreEqual(buddy.AvailableFreeSpace(), 1024_st);
            Assert::ExpectException<std::bad_alloc>(
              [&]() { buddy.allocate(2000); });
          }

          TEST_METHOD(SingleAllocationOf64Bytes)
          {
            donno::Buddy buddy;
            buddy.allocate(64);
            Assert::AreEqual(buddy.AvailableFreeSpace(), 1024_st - 64_st);
          }

          TEST_METHOD(SingleAllocationOf64BytesViaRounding)
          {
            donno::Buddy buddy;
            buddy.allocate(60); // This will still use 64-bytes.
            Assert::AreEqual(buddy.AvailableFreeSpace(), 1024_st - 64_st);
          }

          TEST_METHOD(SingleAllocationOf32Bytes)
          {
            donno::Buddy buddy;
            buddy.allocate(32);
            Assert::AreEqual(buddy.AvailableFreeSpace(), 1024_st - 32_st);
          }

          TEST_METHOD(SingleAllocationOf32BytesViaRounding)
          {
            // This does not use 16-bytes because the smallest allocatable block is 
            // 32-bytes.
            donno::Buddy buddy;
            buddy.allocate(16);
            Assert::AreEqual(buddy.AvailableFreeSpace(), 1024_st - 32_st);
          }

          TEST_METHOD(AllocateEvery32ByteBlock)
          {
            donno::Buddy buddy;
            Assert::AreEqual(buddy.AvailableFreeSpace(), 1024_st);
            while (buddy.AvailableFreeSpace() / 32 > 0)
            {
              buddy.allocate(32);
            }
            Assert::AreEqual(buddy.AvailableFreeSpace(), 0_st);
          }
	};
}