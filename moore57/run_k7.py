"""Driver: exact structure counts and brute-force cost at k = 7."""
import general_search

print("--- exact counts of valid t-block structures, k = 7, t <= 4 ---",
      flush=True)
general_search.report(7, count_all=True, depth_limit=4)
print(flush=True)
print("--- first complete solution: how much brute force does k = 7 cost? ---",
      flush=True)
general_search.report(7, count_all=False)
