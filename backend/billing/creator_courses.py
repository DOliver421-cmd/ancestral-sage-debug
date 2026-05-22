"""
Creator Course System
Allow creators to build, price, and sell their own courses at tiered, affordable rates.
Revenue sharing: Creator gets 70%, WAI gets 30%
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class CourseType(str, Enum):
    """Types of creator courses"""
    WORKSHOP = "workshop"       # Single session, 1-3 hours
    MINI_COURSE = "mini"        # 2-5 lessons
    FULL_COURSE = "full"        # 6+ lessons
    CERTIFICATION = "cert"      # With completion certificate


CREATOR_COURSE_PRICING = {
    # PHASE 1: LAUNCH PRICING (Super Cheap - Build Audience)
    "workshop": {
        "name": "Workshop (1-3 hours)",
        "base_price": 1.99,          # SUPER CHEAP
        "current_price": 1.99,
        "creator_earnings": 1.39,    # 70%
        "wai_earnings": 0.60,        # 30%
        "description": "Single session, live or recorded",
        "max_lessons": 1,
        "enrollment_threshold": None,  # Price increases at this enrollment count
        "next_price": 2.99,           # Price after threshold
    },
    "mini": {
        "name": "Mini Course (2-5 lessons)",
        "base_price": 3.99,           # SUPER CHEAP
        "current_price": 3.99,
        "creator_earnings": 2.79,     # 70%
        "wai_earnings": 1.20,         # 30%
        "description": "Short, focused training series",
        "max_lessons": 5,
        "enrollment_threshold": 100,   # After 100 students, raise to $4.99
        "next_price": 4.99,
    },
    "full": {
        "name": "Full Course (6+ lessons)",
        "base_price": 7.99,           # SUPER CHEAP
        "current_price": 7.99,
        "creator_earnings": 5.59,     # 70%
        "wai_earnings": 2.40,         # 30%
        "description": "Comprehensive, in-depth curriculum",
        "max_lessons": 999,
        "enrollment_threshold": 200,   # After 200 students, raise to $12.99
        "next_price": 12.99,
    },
    "cert": {
        "name": "Certification Course (with cert)",
        "base_price": 9.99,           # SUPER CHEAP
        "current_price": 9.99,
        "creator_earnings": 6.99,     # 70%
        "wai_earnings": 3.00,         # 30%
        "description": "Includes completion certificate & badge",
        "max_lessons": 999,
        "enrollment_threshold": 150,   # After 150 students, raise to $14.99
        "next_price": 14.99,
    },
}

# Price increase schedule based on demand (students enrolled)
PRICE_ESCALATION_SCHEDULE = {
    # When course reaches this enrollment count, price goes to this level
    "workshop": [
        {"students": 50, "price": 2.99},
        {"students": 200, "price": 3.99},
        {"students": 500, "price": 4.99},
        {"students": 1000, "price": 5.99},
    ],
    "mini": [
        {"students": 100, "price": 4.99},
        {"students": 300, "price": 6.99},
        {"students": 750, "price": 8.99},
        {"students": 1500, "price": 9.99},
    ],
    "full": [
        {"students": 200, "price": 12.99},
        {"students": 500, "price": 16.99},
        {"students": 1000, "price": 19.99},
        {"students": 2000, "price": 24.99},
    ],
    "cert": [
        {"students": 150, "price": 14.99},
        {"students": 400, "price": 19.99},
        {"students": 800, "price": 24.99},
        {"students": 1500, "price": 29.99},
    ],
}


class CreatorCourse(BaseModel):
    """A course created by a creator"""
    creator_id: str
    title: str
    description: str
    course_type: CourseType
    category: str  # "healing", "art", "crafts", "business", "wellness", "education"
    language: str = "en"
    price: float  # Actual price in USD
    lessons: List[dict] = []  # [{"title": "...", "content": "...", "duration_minutes": 30}, ...]
    cover_image_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    students_enrolled: int = 0
    total_revenue: float = 0.0
    creator_earnings: float = 0.0
    wai_earnings: float = 0.0
    rating: float = 0.0  # 0-5 stars
    reviews_count: int = 0
    published: bool = False
    draft_created_at: datetime = None
    published_at: Optional[datetime] = None
    updated_at: datetime = None
    completion_percentage: float = 0.0  # avg completion rate


class StudentEnrollment(BaseModel):
    """Student enrollment in a creator course"""
    student_id: str
    course_id: str
    creator_id: str
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    completion_percentage: float = 0.0
    lessons_completed: List[str] = []  # Lesson IDs
    last_accessed_at: datetime = None
    review: Optional[str] = None
    rating: Optional[float] = None  # 1-5 stars


class CreatorEarnings(BaseModel):
    """Track creator earnings from courses"""
    creator_id: str
    total_students: int = 0
    total_courses: int = 0
    total_revenue: float = 0.0
    total_earnings: float = 0.0  # Creator's 70%
    total_wai_earnings: float = 0.0  # WAI's 30%
    monthly_revenue: float = 0.0
    monthly_earnings: float = 0.0
    payout_method: str = "stripe_connect"  # or "bank_transfer"
    next_payout_date: Optional[datetime] = None
    last_payout_date: Optional[datetime] = None
    last_payout_amount: float = 0.0


def get_course_price(course_type: str, students_enrolled: int) -> dict:
    """Calculate current price based on demand (students enrolled)"""
    if course_type not in PRICE_ESCALATION_SCHEDULE:
        return None

    base = CREATOR_COURSE_PRICING[course_type]
    schedule = PRICE_ESCALATION_SCHEDULE[course_type]

    # Find applicable price tier based on enrollment
    current_price = base["base_price"]
    for tier in schedule:
        if students_enrolled >= tier["students"]:
            current_price = tier["price"]

    creator_earnings = current_price * 0.7
    wai_earnings = current_price * 0.3

    return {
        "course_type": course_type,
        "students_enrolled": students_enrolled,
        "current_price": current_price,
        "creator_earnings": round(creator_earnings, 2),
        "wai_earnings": round(wai_earnings, 2),
        "next_price_at": None,  # Will be set if there's a next tier
    }


async def init_creator_courses(db: AsyncIOMotorDatabase) -> dict:
    """Initialize creator course collections"""
    try:
        # Creator courses
        await db.creator_courses.create_index("creator_id")
        await db.creator_courses.create_index([("published", 1), ("published_at", -1)])
        await db.creator_courses.create_index([("category", 1), ("rating", -1)])
        await db.creator_courses.create_index([("language", 1), ("published", 1)])
        await db.creator_courses.create_index("title")

        # Student enrollments
        await db.student_enrollments.create_index([("student_id", 1), ("course_id", 1)], unique=True)
        await db.student_enrollments.create_index([("course_id", 1)])
        await db.student_enrollments.create_index([("creator_id", 1)])
        await db.student_enrollments.create_index([("enrolled_at", -1)])

        # Creator earnings
        await db.creator_earnings.create_index("creator_id", unique=True)
        await db.creator_earnings.create_index([("total_earnings", -1)])
        await db.creator_earnings.create_index([("monthly_earnings", -1)])

        # Course reviews
        await db.course_reviews.create_index([("course_id", 1)])
        await db.course_reviews.create_index([("rating", -1)])
        await db.course_reviews.create_index([("created_at", -1)])

        logger.info("✅ Creator course collections initialized")
        return {"status": "success"}
    except Exception as e:
        logger.warning(f"Creator courses init (non-fatal): {e}")
        return {"status": "partial", "error": str(e)}


async def create_course(
    db: AsyncIOMotorDatabase,
    creator_id: str,
    title: str,
    description: str,
    course_type: str,
    category: str,
    language: str = "en",
) -> dict:
    """Create a new course draft"""
    if course_type not in CREATOR_COURSE_PRICING:
        return {"status": "error", "message": f"Invalid course type: {course_type}"}

    pricing = CREATOR_COURSE_PRICING[course_type]

    course_doc = {
        "creator_id": creator_id,
        "title": title,
        "description": description,
        "course_type": course_type,
        "category": category,
        "language": language,
        "base_price": pricing["base_price"],       # Base launch price
        "current_price": pricing["base_price"],     # Current price (increases with demand)
        "lessons": [],
        "cover_image_url": None,
        "preview_video_url": None,
        "students_enrolled": 0,
        "total_revenue": 0.0,
        "creator_earnings": 0.0,
        "wai_earnings": 0.0,
        "rating": 0.0,
        "reviews_count": 0,
        "published": False,
        "draft_created_at": datetime.utcnow(),
        "published_at": None,
        "updated_at": datetime.utcnow(),
        "completion_percentage": 0.0,
    }

    result = await db.creator_courses.insert_one(course_doc)
    logger.info(f"Created course draft for {creator_id}: {title} (base price: ${pricing['base_price']})")

    # Initialize creator earnings if not exists
    await db.creator_earnings.update_one(
        {"creator_id": creator_id},
        {
            "$setOnInsert": {
                "creator_id": creator_id,
                "total_students": 0,
                "total_courses": 0,
                "total_revenue": 0.0,
                "total_earnings": 0.0,
                "total_wai_earnings": 0.0,
                "monthly_revenue": 0.0,
                "monthly_earnings": 0.0,
                "payout_method": "stripe_connect",
                "next_payout_date": None,
                "last_payout_date": None,
                "last_payout_amount": 0.0,
            }
        },
        upsert=True,
    )

    return {
        "status": "success",
        "course_id": str(result.inserted_id),
        "course_type": course_type,
        "base_price": pricing["base_price"],
        "current_price": pricing["base_price"],
    }


async def add_lesson(
    db: AsyncIOMotorDatabase,
    course_id: str,
    title: str,
    content: str,
    duration_minutes: int,
) -> dict:
    """Add a lesson to a course"""
    from bson import ObjectId

    course = await db.creator_courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        return {"status": "error", "message": "Course not found"}

    if course["published"]:
        return {"status": "error", "message": "Cannot edit published course"}

    course_type = course["course_type"]
    max_lessons = CREATOR_COURSE_PRICING[course_type]["max_lessons"]

    if len(course.get("lessons", [])) >= max_lessons:
        return {"status": "error", "message": f"Max {max_lessons} lessons for {course_type}"}

    lesson = {
        "id": f"lesson_{len(course.get('lessons', []))}",
        "title": title,
        "content": content,
        "duration_minutes": duration_minutes,
        "created_at": datetime.utcnow(),
    }

    await db.creator_courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$push": {"lessons": lesson}, "$set": {"updated_at": datetime.utcnow()}},
    )

    logger.info(f"Added lesson to {course_id}: {title}")
    return {"status": "success", "lesson_id": lesson["id"]}


async def publish_course(db: AsyncIOMotorDatabase, course_id: str) -> dict:
    """Publish a course (make it available for purchase)"""
    from bson import ObjectId

    course = await db.creator_courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        return {"status": "error", "message": "Course not found"}

    if len(course.get("lessons", [])) == 0:
        return {"status": "error", "message": "Course must have at least one lesson"}

    if not course.get("description"):
        return {"status": "error", "message": "Course must have description"}

    await db.creator_courses.update_one(
        {"_id": ObjectId(course_id)},
        {
            "$set": {
                "published": True,
                "published_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        },
    )

    logger.info(f"Published course {course_id}")
    return {"status": "success", "message": "Course published"}


async def enroll_student(
    db: AsyncIOMotorDatabase,
    student_id: str,
    course_id: str,
) -> dict:
    """Enroll student in a course"""
    from bson import ObjectId

    course = await db.creator_courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        return {"status": "error", "message": "Course not found"}

    if not course["published"]:
        return {"status": "error", "message": "Course not published"}

    # Check if already enrolled
    existing = await db.student_enrollments.find_one(
        {"student_id": student_id, "course_id": course_id}
    )
    if existing:
        return {"status": "error", "message": "Already enrolled"}

    enrollment = {
        "student_id": student_id,
        "course_id": course_id,
        "creator_id": course["creator_id"],
        "enrolled_at": datetime.utcnow(),
        "completed_at": None,
        "completion_percentage": 0.0,
        "lessons_completed": [],
        "last_accessed_at": None,
        "review": None,
        "rating": None,
    }

    await db.student_enrollments.insert_one(enrollment)

    # Update course stats
    await db.creator_courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$inc": {"students_enrolled": 1}},
    )

    # Update creator earnings
    await db.creator_earnings.update_one(
        {"creator_id": course["creator_id"]},
        {"$inc": {"total_students": 1}},
    )

    logger.info(f"Student {student_id} enrolled in {course_id}")
    return {"status": "success", "message": "Enrolled"}


async def record_course_completion(
    db: AsyncIOMotorDatabase,
    student_id: str,
    course_id: str,
) -> dict:
    """Mark course as completed"""
    enrollment = await db.student_enrollments.find_one(
        {"student_id": student_id, "course_id": course_id}
    )
    if not enrollment:
        return {"status": "error", "message": "Enrollment not found"}

    await db.student_enrollments.update_one(
        {"student_id": student_id, "course_id": course_id},
        {
            "$set": {
                "completed_at": datetime.utcnow(),
                "completion_percentage": 100.0,
            }
        },
    )

    logger.info(f"Student {student_id} completed {course_id}")
    return {"status": "success"}


async def get_creator_dashboard(db: AsyncIOMotorDatabase, creator_id: str) -> dict:
    """Get creator dashboard with all course stats"""
    courses = await db.creator_courses.find({"creator_id": creator_id}).to_list(None)
    earnings = await db.creator_earnings.find_one({"creator_id": creator_id})

    if not earnings:
        return {"status": "error", "message": "Creator not found"}

    published_courses = [c for c in courses if c["published"]]
    draft_courses = [c for c in courses if not c["published"]]

    return {
        "status": "success",
        "creator_id": creator_id,
        "total_courses": len(courses),
        "published_courses": len(published_courses),
        "draft_courses": len(draft_courses),
        "courses": [
            {
                "id": str(c["_id"]),
                "title": c["title"],
                "type": c["course_type"],
                "price": c["price"],
                "students": c["students_enrolled"],
                "revenue": c["total_revenue"],
                "creator_earnings": c["creator_earnings"],
                "rating": c["rating"],
                "published": c["published"],
            }
            for c in courses
        ],
        "earnings": {
            "total_students": earnings["total_students"],
            "total_revenue": earnings["total_revenue"],
            "total_earnings": earnings["total_earnings"],
            "monthly_revenue": earnings["monthly_revenue"],
            "monthly_earnings": earnings["monthly_earnings"],
            "last_payout_date": earnings.get("last_payout_date"),
            "next_payout_date": earnings.get("next_payout_date"),
        },
    }


async def get_marketplace(
    db: AsyncIOMotorDatabase,
    category: str = None,
    language: str = "en",
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """Get published courses for student marketplace"""
    filter_dict = {"published": True}
    if category:
        filter_dict["category"] = category
    if language:
        filter_dict["language"] = language

    courses = await db.creator_courses.find(filter_dict).skip(skip).limit(limit).to_list(limit)
    total = await db.creator_courses.count_documents(filter_dict)

    return {
        "status": "success",
        "total": total,
        "courses": [
            {
                "id": str(c["_id"]),
                "title": c["title"],
                "description": c["description"],
                "creator_id": c["creator_id"],
                "type": c["course_type"],
                "price": c["price"],
                "category": c["category"],
                "language": c["language"],
                "lessons_count": len(c.get("lessons", [])),
                "students": c["students_enrolled"],
                "rating": c["rating"],
                "reviews_count": c["reviews_count"],
                "cover_image": c.get("cover_image_url"),
                "published_at": c.get("published_at"),
            }
            for c in courses
        ],
    }
