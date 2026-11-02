import re

from src.linkedin.ingest import JobDetails


class TweetGenerator:
    """Build X-ready job posts using X's 23-character URL weighting."""

    URL_PATTERN = re.compile(r"https?://[^\s]+")

    @classmethod
    def get_x_length(cls, text: str) -> int:
        return len(cls.URL_PATTERN.sub("x" * 23, text))

    def generate_tweet(self, job: JobDetails) -> str:
        role_lower = (job.role or "").lower()
        if any(term in role_lower for term in ("ai", "ml", "machine learning", "deep learning", "nlp", "llm", "vision")):
            emoji, category_tag = "🤖", "#AI"
        elif "data" in role_lower:
            emoji, category_tag = "📊", "#Data"
        elif any(term in role_lower for term in ("stack", "backend", "frontend", "dev", "engineer", "code", "programmer")):
            emoji, category_tag = "💻", "#Dev"
        elif any(term in role_lower for term in ("product", "pm")):
            emoji, category_tag = "🎯", "#PM"
        else:
            emoji, category_tag = "💼", "#Tech"

        fields = {
            "role": job.role or "Open role",
            "company": job.company or "Unspecified",
            "location": job.location or "Not specified",
            "experience": job.experience_level or "Not specified",
            "salary": job.salary,
            "link": job.apply_link or "",
        }

        def build(include_salary=True, include_tags=True):
            lines = [
                f"{emoji} Job Alert: {fields['role']}",
                f"🏢 Company: {fields['company']}",
                f"📍 Location: {fields['location']}",
                f"💼 Exp: {fields['experience']}",
            ]
            if include_salary and fields["salary"]:
                lines.append(f"💰 Salary: {fields['salary']}")
            if fields["link"]:
                lines.append(f"\n🔗 Apply: {fields['link']}")
            if include_tags:
                lines.append(f"\n#IndiaJobs #TechHiring {category_tag}")
            return "\n".join(lines)

        # Prefer the complete announcement, then progressively remove optional content.
        for include_salary, include_tags in ((True, True), (False, True), (False, False)):
            candidate = build(include_salary, include_tags)
            if self.get_x_length(candidate) <= 280:
                return candidate

        # Bound user-controlled fields so even malformed posts cannot create oversized drafts.
        for field, limit in (("role", 55), ("company", 35), ("location", 35), ("experience", 24), ("salary", 28)):
            value = fields[field]
            if value and len(value) > limit:
                fields[field] = value[: limit - 3].rstrip() + "..."

        candidate = build(include_salary=False, include_tags=False)
        # Keep the application link intact; trim the descriptive lines if needed.
        for field in ("location", "experience", "company", "role"):
            while self.get_x_length(candidate) > 280 and len(fields[field]) > 12:
                fields[field] = fields[field][: max(9, len(fields[field]) - 8)].rstrip() + "..."
                candidate = build(include_salary=False, include_tags=False)

        if self.get_x_length(candidate) <= 280:
            return candidate

        # Last-resort compact format; preserve the destination link.
        link_line = f"\n🔗 Apply: {fields['link']}" if fields["link"] else ""
        prefix = f"{emoji} {fields['role'][:40]} at {fields['company'][:25]}"
        suffix = f" | {fields['location'][:25]}"
        compact = prefix + suffix + link_line
        while self.get_x_length(compact) > 280 and len(suffix) > 5:
            suffix = suffix[:-4] + "..."
            compact = prefix + suffix + link_line
        while self.get_x_length(compact) > 280 and len(prefix) > 12:
            prefix = prefix[:-4] + "..."
            compact = prefix + suffix + link_line
        return compact
