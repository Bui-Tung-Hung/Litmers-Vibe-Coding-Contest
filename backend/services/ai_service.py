import google.generativeai as genai
from backend.config import get_settings
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.notification import AIRateLimit
from fastapi import HTTPException, status

settings = get_settings()

# Configure Gemini
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)


def check_rate_limit(db: Session, user_id: int) -> bool:
    """Check if user has exceeded AI rate limit (10 requests per minute)"""
    current_minute = datetime.utcnow().replace(second=0, microsecond=0)
    
    # Get or create rate limit record
    rate_limit = db.query(AIRateLimit).filter(
        AIRateLimit.user_id == user_id,
        AIRateLimit.minute_window == current_minute
    ).first()
    
    if not rate_limit:
        # Create new record
        rate_limit = AIRateLimit(
            user_id=user_id,
            minute_window=current_minute,
            request_count=0
        )
        db.add(rate_limit)
        db.commit()
    
    # Check limit
    if rate_limit.request_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI rate limit exceeded. Maximum 10 requests per minute. Please try again later."
        )
    
    # Increment count
    rate_limit.request_count += 1
    db.commit()
    
    return True


async def generate_summary(description: str) -> str:
    """Generate a 2-4 sentence summary of an issue description"""
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured"
        )
    
    if len(description) <= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must be more than 10 characters"
        )
    
    try:
        model = genai.GenerativeModel(settings.gemini_model)
        prompt = f"""Summarize the following issue description in 2-4 concise sentences. 
Focus on the main problem and key points.

Issue Description:
{description}

Summary:"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


async def generate_suggestion(title: str, description: str) -> str:
    """Generate solution suggestions for an issue"""
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured"
        )
    
    if len(description) <= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must be more than 10 characters"
        )
    
    try:
        model = genai.GenerativeModel(settings.gemini_model)
        prompt = f"""Suggest an approach to solve this issue. Provide practical steps or recommendations.

Issue Title: {title}

Issue Description:
{description}

Solution Approach:"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


async def recommend_labels(title: str, description: str, available_labels: list) -> list:
    """Recommend appropriate labels based on title and description"""
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured"
        )
    
    if not available_labels:
        return []
    
    try:
        model = genai.GenerativeModel(settings.gemini_model)
        label_names = [label["name"] for label in available_labels]
        
        prompt = f"""Based on the following issue, recommend up to 3 most relevant labels from the available list.
Only return the label names separated by commas, nothing else.

Issue Title: {title}
Issue Description: {description}

Available Labels: {", ".join(label_names)}

Recommended Labels (max 3):"""
        
        response = model.generate_content(prompt)
        recommended_names = [name.strip() for name in response.text.strip().split(",")]
        
        # Match with actual labels
        recommended = []
        for label in available_labels:
            if label["name"] in recommended_names and len(recommended) < 3:
                recommended.append(label)
        
        return recommended
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


async def detect_duplicates(title: str, existing_issues: list) -> list:
    """Detect similar issues based on title"""
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured"
        )
    
    if not existing_issues:
        return []
    
    try:
        model = genai.GenerativeModel(settings.gemini_model)
        
        # Prepare issue list
        issue_list = "\n".join([f"{i+1}. {issue['title']}" for i, issue in enumerate(existing_issues)])
        
        prompt = f"""Compare the following new issue title with existing issues and identify potential duplicates.
Return only the numbers of similar issues (e.g., "1, 3, 5"), or "none" if no duplicates found.

New Issue: {title}

Existing Issues:
{issue_list}

Similar Issues (numbers only):"""
        
        response = model.generate_content(prompt)
        result_text = response.text.strip().lower()
        
        if result_text == "none" or not result_text:
            return []
        
        # Parse numbers
        similar_indices = []
        for part in result_text.split(","):
            try:
                idx = int(part.strip()) - 1
                if 0 <= idx < len(existing_issues):
                    similar_indices.append(idx)
            except:
                continue
        
        # Return similar issues (max 3)
        similar_issues = [existing_issues[i] for i in similar_indices[:3]]
        return similar_issues
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


async def summarize_comments(comments: list) -> str:
    """Summarize discussion from comments (requires >= 5 comments)"""
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured"
        )
    
    if len(comments) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 5 comments required for summary"
        )
    
    try:
        model = genai.GenerativeModel(settings.gemini_model)
        
        # Prepare comments text
        comments_text = "\n\n".join([
            f"{comment['user']['name']}: {comment['content']}"
            for comment in comments
        ])
        
        prompt = f"""Summarize the following discussion in 3-5 sentences. 
Highlight key points, decisions made, and any action items.

Discussion:
{comments_text}

Summary:"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )
