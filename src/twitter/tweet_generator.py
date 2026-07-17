import re
from typing import Optional
from src.linkedin.ingest import JobDetails

class TweetGenerator:
    """
    Converts parsed job information into highly engaging, tech-oriented tweets.
    Guarantees tweet length is strictly below 280 characters, accounting for X's
    t.co shortener counting all URLs as 23 characters.
    """
    @staticmethod
    def get_x_length(text: str) -> int:
        """
        Calculates the length of the tweet as X (Twitter) would, where any URL
        is counted as exactly 23 characters.
        """
        # Regex to find standard http/https URLs
        url_pattern = r"https?://[^\s]+"
        # Replace URLs with a 23-character dummy string
        simulated_text = re.sub(url_pattern, "x" * 23, text)
        return len(simulated_text)

    def generate_tweet(self, job: JobDetails) -> str:
        """
        Generates a tweet string from JobDetails and applies progressive
        truncation rules if the length exceeds 280 characters.
        """
        role_lower = job.role.lower()
        
        # Determine emoji and category hashtag
        if any(term in role_lower for term in ["ai", "ml", "machine learning", "deep learning", "nlp", "llm", "vision"]):
            emoji = "🤖"
            category_tag = "#AI"
        elif "data" in role_lower:
            emoji = "📊"
            category_tag = "#Data"
        elif any(term in role_lower for term in ["stack", "backend", "frontend", "dev", "engineer", "code", "coder", "programmer"]):
            emoji = "💻"
            category_tag = "#Dev"
        elif any(term in role_lower for term in ["product", "pm"]):
            emoji = "🎯"
            category_tag = "#PM"
        else:
            emoji = "💼"
            category_tag = "#Tech"

        role = job.role
        company = job.company
        location = job.location
        exp = job.experience_level
        salary = job.salary
        link = job.apply_link or ""

        def build_text(r: str, c: str, include_salary: bool, include_tags: bool) -> str:
            lines = [
                f"{emoji} Job Alert: {r}",
                f"🏢 Company: {c}",
                f"📍 Location: {location}",
                f"💼 Exp: {exp}"
            ]
            if include_salary and salary:
                lines.append(f"💰 Salary: {salary}")
            
            if link:
                lines.append(f"\n🔗 Apply: {link}")
            
            text = "\n".join(lines)
            if include_tags:
                text += f"\n\n#IndiaJobs #TechHiring {category_tag}"
            return text

        # Step 1: Attempt full tweet (with salary & tags)
        tweet = build_text(role, company, include_salary=True, include_tags=True)
        if self.get_x_length(tweet) <= 280:
            return tweet

        # Step 2: Try without tags
        tweet = build_text(role, company, include_salary=True, include_tags=False)
        if self.get_x_length(tweet) <= 280:
            return tweet

        # Step 3: Try without salary
        tweet = build_text(role, company, include_salary=False, include_tags=False)
        if self.get_x_length(tweet) <= 280:
            return tweet

        # Step 4: Iteratively truncate role and company to fit
        max_role_len = 50
        max_company_len = 30
        
        while self.get_x_length(tweet) > 280:
            if len(role) > max_role_len:
                role = role[:max_role_len - 3].strip() + "..."
            elif len(company) > max_company_len:
                company = company[:max_company_len - 3].strip() + "..."
            else:
                # Aggressive fallback truncation if still too long (e.g. extremely long location or exp)
                if len(role) > 15:
                    role = role[:len(role) - 10].strip() + "..."
                elif len(company) > 15:
                    company = company[:len(company) - 10].strip() + "..."
                else:
                    break  # Stop infinite loops, return whatever we managed
            
            tweet = build_text(role, company, include_salary=False, include_tags=False)

        return tweet
