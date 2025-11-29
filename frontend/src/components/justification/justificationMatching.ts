import type { ExistingProduct, SavingProduct } from "../../api/justificationApi";

export function findMatchingSavingProductForExisting(
  product: ExistingProduct | null,
  savingProducts: SavingProduct[]
): SavingProduct | null {
  if (!product) {
    return null;
  }

  const normalizeText = (value: string | null | undefined): string => {
    return (value ?? "").toLowerCase().replace(/\s+/g, " ").trim();
  };

  const normalizeName = (value: string | null | undefined): string => {
    const base = normalizeText(value);
    return base.replace(/["'`.,]/g, "").replace(/\s+/g, " ").trim();
  };

  const normalizeCode = (value: string | null | undefined): string => {
    return (value ?? "").toLowerCase().replace(/[\s-]/g, "");
  };

  const normalizeFundType = (value: string | null | undefined): string => {
    const base = normalizeText(value);
    if (!base) {
      return "";
    }

    if (base.includes("השתלמות")) {
      return "השתלמות";
    }

    return base;
  };

  const normalizeCompanyKey = (value: string | null | undefined): string => {
    const base = normalizeText(value);
    if (!base) {
      return "";
    }

    const parts = base.split(" ").filter(Boolean);
    if (parts.length === 0) {
      return "";
    }

    const significant = parts.find((p) => p.length >= 3) || parts[0];
    return significant;
  };

  const existingCompany = normalizeName(product.companyName);
  const existingCompanyKey = normalizeCompanyKey(product.companyName);
  const existingFundName = normalizeName(product.fundName);
  const existingFundCode = normalizeCode(product.fundCode);
  const existingFundType = normalizeFundType(product.fundType);

  let bestScore = 0;
  let bestProduct: SavingProduct | null = null;

  const splitToWords = (value: string): string[] => {
    return value
      .split(" ")
      .map((part) => part.trim())
      .filter((part) => part.length >= 2);
  };

  savingProducts.forEach((marketProduct) => {
    const marketCompany = normalizeName(marketProduct.companyName);
    const marketCompanyKey = normalizeCompanyKey(marketProduct.companyName);
    const marketFundName = normalizeName(marketProduct.fundName);
    const marketFundCode = normalizeCode(marketProduct.fundCode);
    const marketFundType = normalizeFundType(marketProduct.fundType);

    let score = 0;
    let codeScore = 0;

    if (existingFundCode && marketFundCode) {
      if (existingFundCode === marketFundCode) {
        codeScore += 80;
      } else if (
        existingFundCode.length >= 4 &&
        marketFundCode.length >= 4 &&
        (existingFundCode.includes(marketFundCode) ||
          marketFundCode.includes(existingFundCode))
      ) {
        codeScore += 50;
      }
    }

    score += codeScore;

    if (existingCompany && marketCompany) {
      if (existingCompany === marketCompany) {
        score += 30;
      } else if (
        existingCompany.length >= 4 &&
        marketCompany.length >= 4 &&
        (existingCompany.includes(marketCompany) ||
          marketCompany.includes(existingCompany))
      ) {
        score += 15;
      }
    }

    if (existingCompanyKey && marketCompanyKey && existingCompanyKey === marketCompanyKey) {
      score += 20;
    }

    if (existingFundName && marketFundName) {
      if (existingFundName === marketFundName) {
        score += 25;
      } else if (
        existingFundName.length >= 6 &&
        marketFundName.length >= 6 &&
        (existingFundName.includes(marketFundName) ||
          marketFundName.includes(existingFundName))
      ) {
        score += 10;
      }

      const existingWords = splitToWords(existingFundName);
      const marketWords = splitToWords(marketFundName);
      if (existingWords.length > 0 && marketWords.length > 0) {
        const existingSet = new Set(existingWords);
        let overlapCount = 0;
        marketWords.forEach((w) => {
          if (existingSet.has(w)) {
            overlapCount += 1;
          }
        });

        if (overlapCount >= 3) {
          score += 20;
        } else if (overlapCount === 2) {
          score += 12;
        } else if (overlapCount === 1) {
          score += 5;
        }
      }
    }

    if (existingFundType && marketFundType && existingFundType === marketFundType) {
      score += 10;
    }

    const candidateHasCodeMatch = codeScore > 0;
    const candidateMinScore = candidateHasCodeMatch ? 60 : 30;

    if (score >= candidateMinScore && score > bestScore) {
      bestScore = score;
      bestProduct = marketProduct;
    }
  });

  if (bestProduct) {
    return bestProduct;
  }

  return null;
}
