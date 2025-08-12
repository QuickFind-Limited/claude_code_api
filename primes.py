def is_prime(n):
    """
    Check if a number is prime.
    
    Args:
        n (int): The number to check
        
    Returns:
        bool: True if n is prime, False otherwise
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Check odd divisors up to sqrt(n)
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def generate_primes(limit):
    """
    Generate all prime numbers up to a given limit.
    
    Args:
        limit (int): The upper limit to find primes up to
        
    Returns:
        list: A list of prime numbers up to the limit
    """
    primes = []
    for num in range(2, limit + 1):
        if is_prime(num):
            primes.append(num)
    return primes


def sieve_of_eratosthenes(limit):
    """
    Generate prime numbers using the Sieve of Eratosthenes algorithm.
    More efficient for finding many primes.
    
    Args:
        limit (int): The upper limit to find primes up to
        
    Returns:
        list: A list of prime numbers up to the limit
    """
    if limit < 2:
        return []
    
    # Create a boolean array and initialize all entries as True
    is_prime_array = [True] * (limit + 1)
    is_prime_array[0] = is_prime_array[1] = False
    
    p = 2
    while p * p <= limit:
        if is_prime_array[p]:
            # Mark all multiples of p as not prime
            for i in range(p * p, limit + 1, p):
                is_prime_array[i] = False
        p += 1
    
    # Collect all prime numbers
    primes = [i for i in range(2, limit + 1) if is_prime_array[i]]
    return primes


if __name__ == "__main__":
    # Example usage
    print("Prime numbers up to 30:")
    primes_30 = generate_primes(30)
    print(primes_30)
    
    print("\nUsing Sieve of Eratosthenes for primes up to 50:")
    primes_50 = sieve_of_eratosthenes(50)
    print(primes_50)
    
    print("\nChecking if specific numbers are prime:")
    test_numbers = [17, 25, 29, 100]
    for num in test_numbers:
        print(f"{num} is {'prime' if is_prime(num) else 'not prime'}")