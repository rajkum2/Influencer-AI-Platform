"""
Database seeding script for initial data.
Run with: python -m backend.alembic.seed_data
"""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.base import SessionLocal
from app.models.content import ContentItem
from app.models.influencer import Influencer, SocialAccount
from app.models.technology import Technology, InfluencerTechnology
from app.models.user import Team, User


async def seed_technologies(db: AsyncSession):
    """Seed technology taxonomy."""
    
    technologies = [
        # AI Foundation
        {"name": "Large Language Models", "slug": "llms", "description": "GPT, Claude, LLaMA, and other foundation models", "keywords": ["llm", "gpt", "claude", "foundation model"], "color": "#3B82F6"},
        {"name": "AI Agents", "slug": "ai-agents", "description": "Autonomous AI agents and agent frameworks", "keywords": ["agent", "autonomous", "agentic"], "color": "#8B5CF6"},
        {"name": "Retrieval-Augmented Generation", "slug": "rag", "description": "RAG systems and vector search", "keywords": ["rag", "retrieval", "vector search"], "color": "#10B981"},
        {"name": "Vector Databases", "slug": "vector-db", "description": "Pinecone, Weaviate, Qdrant, and vector stores", "keywords": ["vector", "embedding", "similarity search"], "color": "#F59E0B"},
        
        # Infrastructure
        {"name": "AI Infrastructure", "slug": "ai-infra", "description": "MLOps, deployment, and scaling", "keywords": ["mlops", "deployment", "infrastructure"], "color": "#EF4444"},
        {"name": "GPU & Cloud", "slug": "gpu-cloud", "description": "GPU computing and cloud AI services", "keywords": ["gpu", "cuda", "cloud", "compute"], "color": "#6366F1"},
        {"name": "Fine-tuning", "slug": "fine-tuning", "description": "Model fine-tuning and adaptation", "keywords": ["fine-tune", "lora", "qlora", "peft"], "color": "#EC4899"},
        
        # Applications
        {"name": "AI Coding", "slug": "ai-coding", "description": "Code generation and developer tools", "keywords": ["code", "copilot", "devin", "programming"], "color": "#14B8A6"},
        {"name": "Computer Vision", "slug": "computer-vision", "description": "Image and video AI", "keywords": ["vision", "image", "video", "diffusion"], "color": "#F97316"},
        {"name": "Multimodal AI", "slug": "multimodal", "description": "Vision-language models and multimodal systems", "keywords": ["multimodal", "vlm", "vision-language"], "color": "#84CC16"},
        {"name": "Voice AI", "slug": "voice-ai", "description": "Speech recognition and synthesis", "keywords": ["voice", "speech", "tts", "asr"], "color": "#06B6D4"},
        {"name": "Robotics", "slug": "robotics", "description": "Embodied AI and robotics", "keywords": ["robot", "embodied", "manipulation"], "color": "#78716C"},
        
        # Domains
        {"name": "AI Safety", "slug": "ai-safety", "description": "AI alignment and safety research", "keywords": ["safety", "alignment", "rlhf"], "color": "#DC2626"},
        {"name": "Open Source AI", "slug": "open-source-ai", "description": "Open source models and tools", "keywords": ["open source", "huggingface", "llama"], "color": "#16A34A"},
        {"name": "AI Products", "slug": "ai-products", "description": "AI product management and strategy", "keywords": ["product", "pm", "strategy"], "color": "#7C3AED"},
    ]
    
    for tech_data in technologies:
        # Check if exists
        from sqlalchemy import select
        result = await db.execute(
            select(Technology).where(Technology.slug == tech_data["slug"])
        )
        if not result.scalar_one_or_none():
            tech = Technology(**tech_data, is_active=True)
            db.add(tech)
    
    await db.commit()
    print(f"✅ Seeded {len(technologies)} technologies")


async def seed_influencers(db: AsyncSession):
    """Seed sample influencers."""
    
    # Get technology IDs
    from sqlalchemy import select
    result = await db.execute(select(Technology))
    techs = {t.slug: t.id for t in result.scalars().all()}
    
    influencers_data = [
        {
            "full_name": "Andrej Karpathy",
            "display_name": "Andrej Karpathy",
            "headline": "AI researcher, previously Director of AI at Tesla, founding member of OpenAI",
            "bio": "I like to train deep neural nets on large datasets.",
            "country_code": "US",
            "region": "North America",
            "role_type": "researcher",
            "company": "Eureka Labs",
            "profile_image_url": "https://i.ytimg.com/vi/VMj-A3Si1xY/maxresdefault.jpg",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "youtube", "handle": "@AndrejKarpathy", "url": "https://youtube.com/@AndrejKarpathy", "followers_count": 500000},
                {"platform": "twitter", "handle": "karpathy", "url": "https://twitter.com/karpathy", "followers_count": 750000},
                {"platform": "github", "handle": "karpathy", "url": "https://github.com/karpathy", "followers_count": 80000},
            ],
            "technologies": ["llms", "ai-agents", "ai-coding", "computer-vision"]
        },
        {
            "full_name": "Yann LeCun",
            "display_name": "Yann LeCun",
            "headline": "Chief AI Scientist at Meta, Turing Award winner, Professor at NYU",
            "bio": "Working on AI, machine learning, computer vision, robotics, image compression.",
            "country_code": "US",
            "region": "North America",
            "role_type": "researcher",
            "company": "Meta",
            "profile_image_url": "https://scontent-sjc3-1.xx.fbcdn.net/v/t1.6435-9/120556167_10157754525652143_4762215721859523595_n.jpg",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "twitter", "handle": "ylecun", "url": "https://twitter.com/ylecun", "followers_count": 900000},
                {"platform": "linkedin", "handle": "yannlecun", "url": "https://linkedin.com/in/yannlecun", "followers_count": 200000},
            ],
            "technologies": ["llms", "computer-vision", "ai-safety", "open-source-ai"]
        },
        {
            "full_name": "Andrew Ng",
            "display_name": "Andrew Ng",
            "headline": "Founder of DeepLearning.AI, Coursera, Landing AI, AI Fund",
            "bio": "Making AI accessible to everyone through education and tools.",
            "country_code": "US",
            "region": "North America",
            "role_type": "educator",
            "company": "DeepLearning.AI",
            "profile_image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Andrew_Ng_at_TechCrunch_Disrupt_SF_2017.jpg/1200px-Andrew_Ng_at_TechCrunch_Disrupt_SF_2017.jpg",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "youtube", "handle": "@Deeplearningai", "url": "https://youtube.com/@Deeplearningai", "followers_count": 250000},
                {"platform": "twitter", "handle": "AndrewYNg", "url": "https://twitter.com/AndrewYNg", "followers_count": 600000},
            ],
            "technologies": ["llms", "ai-infra", "ai-products", "computer-vision"]
        },
        {
            "full_name": "Lex Fridman",
            "display_name": "Lex Fridman",
            "headline": "MIT researcher, podcast host, AI researcher",
            "bio": "I conduct research on AI and host a podcast.",
            "country_code": "US",
            "region": "North America",
            "role_type": "educator",
            "company": "MIT",
            "profile_image_url": "https://i.ytimg.com/vi/jwrRggoN1cY/maxresdefault.jpg",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "youtube", "handle": "@lexfridman", "url": "https://youtube.com/@lexfridman", "followers_count": 4200000},
                {"platform": "twitter", "handle": "lexfridman", "url": "https://twitter.com/lexfridman", "followers_count": 4500000},
            ],
            "technologies": ["llms", "ai-agents", "ai-safety", "robotics"]
        },
        {
            "full_name": "Sebastian Raschka",
            "display_name": "Sebastian Raschka",
            "headline": "Machine Learning researcher and educator",
            "bio": "Author of Machine Learning with PyTorch and Scikit-Learn. Building LLMs from scratch.",
            "country_code": "US",
            "region": "North America",
            "role_type": "educator",
            "company": "Lightning AI",
            "profile_image_url": "https://sebastianraschka.com/images/headshot.jpg",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "twitter", "handle": "rasbt", "url": "https://twitter.com/rasbt", "followers_count": 180000},
                {"platform": "github", "handle": "rasbt", "url": "https://github.com/rasbt", "followers_count": 25000},
                {"platform": "youtube", "handle": "@SebastianRaschka", "url": "https://youtube.com/@SebastianRaschka", "followers_count": 80000},
            ],
            "technologies": ["llms", "open-source-ai", "fine-tuning", "computer-vision"]
        },
        {
            "full_name": "Clem Delangue",
            "display_name": "Clem Delangue",
            "headline": "CEO & Co-founder of Hugging Face",
            "bio": "Democratizing AI through open source.",
            "country_code": "US",
            "region": "North America",
            "role_type": "founder",
            "company": "Hugging Face",
            "profile_image_url": "https://huggingface.co/front/assets/huggingface_logo-noborder.svg",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "twitter", "handle": "ClementDelangue", "url": "https://twitter.com/ClementDelangue", "followers_count": 200000},
                {"platform": "linkedin", "handle": "clementdelangue", "url": "https://linkedin.com/in/clementdelangue", "followers_count": 100000},
            ],
            "technologies": ["open-source-ai", "llms", "multimodal", "ai-infra"]
        },
        {
            "full_name": "Swyx",
            "display_name": "swyx",
            "headline": "Developer, writer, and AI engineer",
            "bio": "Writing about AI engineering and the future of software.",
            "country_code": "US",
            "region": "North America",
            "role_type": "engineer",
            "company": "Smol AI",
            "profile_image_url": "https://avatars.githubusercontent.com/u/6764957?v=4",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "twitter", "handle": "swyx", "url": "https://twitter.com/swyx", "followers_count": 150000},
                {"platform": "github", "handle": "sw-yx", "url": "https://github.com/sw-yx", "followers_count": 15000},
            ],
            "technologies": ["ai-agents", "ai-coding", "ai-products", "llms"]
        },
        {
            "full_name": "Sharon Zhou",
            "display_name": "Sharon Zhou",
            "headline": "Co-founder of Lamini, Stanford CS PhD",
            "bio": "Building the future of LLM infrastructure.",
            "country_code": "US",
            "region": "North America",
            "role_type": "founder",
            "company": "Lamini",
            "profile_image_url": "https://lamini.ai/images/team/sharon.jpg",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "twitter", "handle": "realSharonZhou", "url": "https://twitter.com/realSharonZhou", "followers_count": 50000},
                {"platform": "linkedin", "handle": "sharonzhou", "url": "https://linkedin.com/in/sharonzhou", "followers_count": 30000},
            ],
            "technologies": ["llms", "fine-tuning", "ai-infra", "ai-products"]
        },
        {
            "full_name": "Sandeep Singh",
            "display_name": "Sandeep Singh",
            "headline": "AI researcher and educator from India",
            "bio": "Sharing AI knowledge and building in public.",
            "country_code": "IN",
            "region": "APAC",
            "city": "Bangalore",
            "role_type": "educator",
            "company": "Independent",
            "profile_image_url": "https://randomuser.me/api/portraits/men/32.jpg",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "youtube", "handle": "@codebasics", "url": "https://youtube.com/@codebasics", "followers_count": 2000000},
                {"platform": "twitter", "handle": "sandeep", "url": "https://twitter.com/sandeep", "followers_count": 80000},
            ],
            "technologies": ["llms", "ai-coding", "computer-vision"]
        },
        {
            "full_name": "Emad Mostaque",
            "display_name": "Emad Mostaque",
            "headline": "CEO of Stability AI",
            "bio": "Building the foundation for generative AI.",
            "country_code": "GB",
            "region": "Europe",
            "role_type": "founder",
            "company": "Stability AI",
            "profile_image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Emad_Mostaque.jpg/1200px-Emad_Mostaque.jpg",
            "verification_status": "verified",
            "social_accounts": [
                {"platform": "twitter", "handle": "EMostaque", "url": "https://twitter.com/EMostaque", "followers_count": 120000},
            ],
            "technologies": ["computer-vision", "open-source-ai", "multimodal", "ai-safety"]
        },
    ]
    
    for inf_data in influencers_data:
        # Check if exists
        from sqlalchemy import select
        result = await db.execute(
            select(Influencer).where(Influencer.full_name == inf_data["full_name"])
        )
        if result.scalar_one_or_none():
            continue
        
        social_accounts = inf_data.pop("social_accounts", [])
        tech_slugs = inf_data.pop("technologies", [])
        
        # Calculate total followers
        total_followers = sum(acc.get("followers_count", 0) for acc in social_accounts)
        
        influencer = Influencer(
            **inf_data,
            id=uuid.uuid4(),
            total_followers=total_followers,
            content_count=0,
            is_active=True
        )
        db.add(influencer)
        await db.flush()
        
        # Add social accounts
        for acc_data in social_accounts:
            account = SocialAccount(
                influencer_id=influencer.id,
                **acc_data,
                sync_status="pending"
            )
            db.add(account)
        
        # Add technology mappings
        for slug in tech_slugs:
            if slug in techs:
                mapping = InfluencerTechnology(
                    influencer_id=influencer.id,
                    technology_id=techs[slug],
                    relevance_score=0.8,
                    detection_method="manual"
                )
                db.add(mapping)
    
    await db.commit()
    print(f"✅ Seeded {len(influencers_data)} influencers")


async def seed_content(db: AsyncSession):
    """Seed sample content items."""
    
    from sqlalchemy import select
    
    # Get influencers
    result = await db.execute(select(Influencer))
    influencers = result.scalars().all()
    
    if not influencers:
        print("⚠️ No influencers found, skipping content seeding")
        return
    
    content_samples = [
        {
            "platform": "youtube",
            "content_type": "video",
            "title": "Let's build GPT: from scratch, in code, spelled out.",
            "body_text": "We build GPT from scratch, following the paper 'Attention is All You Need' and OpenAI's GPT-2/GPT-3.",
            "views": 5000000,
            "likes": 150000,
        },
        {
            "platform": "youtube",
            "content_type": "video",
            "title": "Intro to Large Language Models",
            "body_text": "Introduction to large language models covering what they are, how they work, and future directions.",
            "views": 3000000,
            "likes": 100000,
        },
        {
            "platform": "github",
            "content_type": "repo",
            "title": "nanoGPT",
            "body_text": "The simplest, fastest repository for training/finetuning medium-sized GPTs.",
            "views": 50000,
            "likes": 35000,
        },
    ]
    
    # Add content for first few influencers
    for i, influencer in enumerate(influencers[:5]):
        for j, content_data in enumerate(content_samples):
            # Check if exists
            result = await db.execute(
                select(ContentItem).where(
                    (ContentItem.influencer_id == influencer.id) &
                    (ContentItem.title == content_data["title"])
                )
            )
            if result.scalar_one_or_none():
                continue
            
            content = ContentItem(
                id=uuid.uuid4(),
                influencer_id=influencer.id,
                **content_data,
                external_id=f"sample_{i}_{j}",
                original_url=f"https://example.com/content/{i}/{j}",
                published_at=datetime.utcnow() - timedelta(days=j * 7),
                processing_status="completed",
                is_indexed=True
            )
            db.add(content)
    
    await db.commit()
    print(f"✅ Seeded sample content")


async def seed_users(db: AsyncSession):
    """Seed admin user."""
    
    from sqlalchemy import select
    
    # Check if admin exists
    result = await db.execute(
        select(User).where(User.email == "admin@influencer-platform.com")
    )
    if not result.scalar_one_or_none():
        # Create team
        team = Team(
            id=uuid.uuid4(),
            name="Admin Team",
            slug="admin-team",
            plan="enterprise",
            max_influencers=10000,
            max_team_members=50,
            max_watchlists=100
        )
        db.add(team)
        await db.flush()
        
        # Create admin user
        admin = User(
            id=uuid.uuid4(),
            email="admin@influencer-platform.com",
            password_hash=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            role="superadmin",
            team_id=team.id,
            is_active=True,
            email_verified_at=datetime.utcnow()
        )
        db.add(admin)
        
        # Create demo user
        demo = User(
            id=uuid.uuid4(),
            email="demo@influencer-platform.com",
            password_hash=get_password_hash("demo123"),
            first_name="Demo",
            last_name="User",
            role="admin",
            team_id=team.id,
            is_active=True,
            email_verified_at=datetime.utcnow()
        )
        db.add(demo)
        
        await db.commit()
        print("✅ Seeded admin and demo users")
        print("   Admin: admin@influencer-platform.com / admin123")
        print("   Demo:  demo@influencer-platform.com / demo123")


async def seed_all():
    """Run all seeding."""
    
    async with SessionLocal() as db:
        print("🌱 Seeding database...")
        
        await seed_technologies(db)
        await seed_users(db)
        await seed_influencers(db)
        await seed_content(db)
        
        print("\n✨ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_all())
