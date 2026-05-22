"""
Creator Course API Routes
Endpoints for creators to build and sell courses, students to discover and learn.
"""

from fastapi import APIRouter, Request, HTTPException, Query
from datetime import datetime
from .creator_courses import (
    init_creator_courses,
    create_course,
    add_lesson,
    publish_course,
    enroll_student,
    record_course_completion,
    get_creator_dashboard,
    get_marketplace,
    get_course_price,
    CREATOR_COURSE_PRICING,
    PRICE_ESCALATION_SCHEDULE,
    CreatorCourse,
)

router = APIRouter(prefix="/api/creator-courses", tags=["creator-courses"])


@router.get("/pricing")
async def get_pricing():
    """List creator course pricing tiers with escalation schedule"""
    return {
        "status": "success",
        "note": "Prices increase with demand (student enrollment) to reward popular courses",
        "pricing": CREATOR_COURSE_PRICING,
        "escalation_schedule": PRICE_ESCALATION_SCHEDULE,
    }


@router.get("/pricing/{course_type}")
async def get_course_pricing(course_type: str, students: int = Query(0)):
    """Get current price for a course type based on enrollment"""
    price_info = get_course_price(course_type, students)
    if not price_info:
        raise HTTPException(status_code=400, detail=f"Invalid course type: {course_type}")

    return {
        "status": "success",
        "price_info": price_info,
        "escalation_schedule": PRICE_ESCALATION_SCHEDULE.get(course_type, []),
    }


@router.post("/create")
async def create_new_course(
    creator_id: str,
    title: str,
    description: str,
    course_type: str,
    category: str,
    request: Request,
    language: str = "en",
):
    """Create a new course draft"""
    db = request.app.state.db

    if course_type not in CREATOR_COURSE_PRICING:
        raise HTTPException(status_code=400, detail=f"Invalid course type: {course_type}")

    result = await create_course(db, creator_id, title, description, course_type, category, language)
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.get("/course/{course_id}")
async def get_course(course_id: str, request: Request):
    """Get course details"""
    from bson import ObjectId

    db = request.app.state.db
    try:
        course = await db.creator_courses.find_one({"_id": ObjectId(course_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid course ID")

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course["_id"] = str(course["_id"])
    return {"status": "success", "course": course}


@router.post("/course/{course_id}/lesson")
async def add_new_lesson(
    course_id: str,
    title: str,
    content: str,
    duration_minutes: int,
    request: Request,
):
    """Add lesson to course"""
    db = request.app.state.db
    result = await add_lesson(db, course_id, title, content, duration_minutes)
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.post("/course/{course_id}/publish")
async def publish_new_course(course_id: str, request: Request):
    """Publish course (make available for purchase)"""
    db = request.app.state.db
    result = await publish_course(db, course_id)
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.get("/dashboard/{creator_id}")
async def get_creator_stats(creator_id: str, request: Request):
    """Get creator dashboard"""
    db = request.app.state.db
    result = await get_creator_dashboard(db, creator_id)
    if result["status"] != "success":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


@router.get("/marketplace")
async def get_courses(
    request: Request,
    category: str = Query(None),
    language: str = Query("en"),
    skip: int = Query(0),
    limit: int = Query(20),
):
    """Browse published courses (student marketplace)"""
    db = request.app.state.db
    result = await get_marketplace(db, category, language, skip, limit)
    return result


@router.post("/enroll")
async def enroll_in_course(
    student_id: str,
    course_id: str,
    request: Request,
):
    """Enroll student in course"""
    db = request.app.state.db
    result = await enroll_student(db, student_id, course_id)
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.post("/complete")
async def complete_course(
    student_id: str,
    course_id: str,
    request: Request,
):
    """Mark course as completed"""
    db = request.app.state.db
    result = await record_course_completion(db, student_id, course_id)
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.get("/categories")
async def get_categories():
    """List available course categories"""
    return {
        "status": "success",
        "categories": [
            "healing",
            "art",
            "crafts",
            "business",
            "wellness",
            "education",
            "music",
            "poetry",
            "spirituality",
            "community",
        ],
    }


@router.post("/review/{course_id}")
async def submit_review(
    course_id: str,
    student_id: str,
    rating: float,
    review_text: str,
    request: Request,
):
    """Submit course review"""
    from bson import ObjectId

    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    db = request.app.state.db

    # Check enrollment
    enrollment = await db.student_enrollments.find_one(
        {"student_id": student_id, "course_id": course_id}
    )
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in course")

    # Add review
    review_doc = {
        "course_id": course_id,
        "student_id": student_id,
        "rating": rating,
        "review_text": review_text,
        "created_at": datetime.utcnow(),
    }
    await db.course_reviews.insert_one(review_doc)

    # Update enrollment with review
    await db.student_enrollments.update_one(
        {"student_id": student_id, "course_id": course_id},
        {"$set": {"rating": rating, "review": review_text}},
    )

    # Update course rating
    reviews = await db.course_reviews.find({"course_id": course_id}).to_list(None)
    avg_rating = sum(r["rating"] for r in reviews) / len(reviews) if reviews else 0

    await db.creator_courses.update_one(
        {"_id": ObjectId(course_id)},
        {
            "$set": {
                "rating": avg_rating,
                "reviews_count": len(reviews),
            }
        },
    )

    return {
        "status": "success",
        "message": "Review submitted",
        "course_rating": avg_rating,
    }


@router.get("/trending")
async def get_trending_courses(request: Request):
    """Get trending/top-rated courses"""
    db = request.app.state.db

    courses = (
        await db.creator_courses.find({"published": True})
        .sort([("rating", -1), ("students_enrolled", -1)])
        .limit(10)
        .to_list(10)
    )

    return {
        "status": "success",
        "courses": [
            {
                "id": str(c["_id"]),
                "title": c["title"],
                "creator_id": c["creator_id"],
                "price": c["price"],
                "rating": c["rating"],
                "students": c["students_enrolled"],
                "reviews": c["reviews_count"],
            }
            for c in courses
        ],
    }
