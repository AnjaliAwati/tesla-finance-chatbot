# Testing

I tested the chatbot with the same 15 questions in two rounds (`run_tests.py`) and checked every answer against the source PDFs.
Sources: Tesla quarterly shareholder update decks (Q4 2025, Q1, Q2 and Q3 2026). Model: Gemini API. Only the number of retrieved chunks changed between rounds.

| Round | Retrieved chunks (top-k) | Correct | Score |
| ----- | ------------------------ | ------- | ----- |
| 1     | 4                        | 13 / 15 | 87%   |
| 2     | 6                        | 15 / 15 | 100%  |

## Round 2 results (top-6, final app setting)

| #   | Question                                                                           | Source says (file, page)               | Chatbot answer                                | Correct? |
| --- | ---------------------------------------------------------------------------------- | -------------------------------------- | --------------------------------------------- | -------- |
| 1   | What was total revenue in Q3 2026?                                                 | $28,046M (q3, p.4 and p.27)            | $28,046M (q3, p.4)                            | Yes      |
| 2   | How did total revenue in Q3 2026 compare with Q3 2025?                             | $28,046M vs $28,095M, 0% YoY (q3, p.4) | $28,046M vs $28,095M, 0% (q3, p.4)            | Yes      |
| 3   | What was services and other revenue in Q3 2026?                                    | $4,605M (q3, p.4)                      | $4,605M (q3, p.4)                             | Yes      |
| 4   | What was energy generation and storage revenue in Q3 2026?                         | $2,881M (q3, p.4)                      | $2,881M (q3, p.4)                             | Yes      |
| 5   | What was total gross profit in Q3 2026?                                            | $5,494M (q3, p.4)                      | $5,494M (q3, p.4)                             | Yes      |
| 6   | What was research and development expense in Q3 2026?                              | $2,761M (q3, p.27)                     | $2,761M (q3, p.27)                            | Yes      |
| 7   | What was automotive regulatory credits revenue in Q3 2026?                         | $113M (q3, p.27)                       | $113M (q3, p.27)                              | Yes      |
| 8   | What was GAAP net income attributable to common stockholders in Q3 2026?           | $787M (q3, p.4, p.27, p.30)            | $787M (q3, p.30)                              | Yes      |
| 9   | What were cash, cash equivalents and short-term investments at the end of Q3 2026? | $45,447M (q3, p.28)                    | $45,447M (q3, p.28)                           | Yes      |
| 10  | What were total vehicle deliveries in Q3 2026?                                     | 486,532 (q3, p.5)                      | 486,532 (q3, p.5)                             | Yes      |
| 11  | What was free cash flow in Q3 2026?                                                | $1,531M (q3, p.4 and p.31)             | $1,531M (q3, p.31)                            | Yes      |
| 12  | What was total revenue in Q2 2026?                                                 | $28,236M (q2, p.4 and p.27)            | $28,236M (q2, p.4 and p.27)                   | Yes      |
| 13  | What were total deliveries in Q1 2026?                                             | 358,023 (q1, p.5)                      | 358,023 (q1, p.5)                             | Yes      |
| 14  | What will Tesla's stock price be next year?                                        | Not in the documents (should refuse)   | "I couldn't find that in the loaded filings." | Yes      |
| 15  | What was Ford's revenue last quarter?                                              | Not in the documents (should refuse)   | "I couldn't find that in the loaded filings." | Yes      |

## Round 1 (top-4): what failed

- **Q1 and Q12** ("total revenue" in Q3 and Q2 2026): the bot answered "I couldn't find that in the loaded filings."
- **Cause:** retrieval returned the Key Metrics chart pages instead of the Financial Summary table on page 4. The model correctly refused to guess, so this was a retrieval miss, not hallucination.
- **Fix:** retrieving 6 chunks instead of 4 brought page 4 into the results, and both questions were then answered correctly.

## Notes and limits

- Small test set (15 questions), mostly number lookups, so 100% does not mean the bot is always right. Chart-heavy pages still compete with tables in search results.
- Every correct answer cited the right file and page, and out-of-scope questions were refused.
- Each question is answered independently, so follow-up questions need full context.
- The Gemini free tier has a small daily quota, so the app may be temporarily unavailable.
- **Next improvements:** keyword-aware search so tables rank above charts, and a larger test set including text questions.
