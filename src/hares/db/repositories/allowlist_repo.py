from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from hares.db.models import OfficialDomain
from hares.db.seed_data import OFFICIAL_UAE_DOMAINS_SEED, get_default_quarterly_review


class AllowlistRepository:
    """
    Repository for managing and querying official registrable domain records (FR-2.2).
    Provides both asynchronous and synchronous data access patterns.
    """

    @staticmethod
    async def get_active_domains_async(session: AsyncSession) -> list[OfficialDomain]:
        stmt = select(OfficialDomain).where(OfficialDomain.is_active.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def get_active_domains_sync(session: Session) -> list[OfficialDomain]:
        stmt = select(OfficialDomain).where(OfficialDomain.is_active.is_(True))
        result = session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_active_domain_names_async(session: AsyncSession) -> set[str]:
        stmt = select(OfficialDomain.domain).where(OfficialDomain.is_active.is_(True))
        result = await session.execute(stmt)
        return {d.lower().strip() for d in result.scalars().all()}

    @staticmethod
    def get_active_domain_names_sync(session: Session) -> set[str]:
        stmt = select(OfficialDomain.domain).where(OfficialDomain.is_active.is_(True))
        result = session.execute(stmt)
        return {d.lower().strip() for d in result.scalars().all()}

    @staticmethod
    async def get_domain_by_name_async(session: AsyncSession, domain: str) -> OfficialDomain | None:
        stmt = select(OfficialDomain).where(
            OfficialDomain.domain == domain.strip().lower(),
            OfficialDomain.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def get_domain_by_name_sync(session: Session, domain: str) -> OfficialDomain | None:
        stmt = select(OfficialDomain).where(
            OfficialDomain.domain == domain.strip().lower(),
            OfficialDomain.is_active.is_(True),
        )
        result = session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def seed_default_domains_async(session: AsyncSession) -> int:
        """Seeds initial verified UAE domains if not already present."""
        existing = await AllowlistRepository.get_active_domain_names_async(session)
        inserted = 0
        review_date = get_default_quarterly_review()

        for item in OFFICIAL_UAE_DOMAINS_SEED:
            norm_domain = item["domain"].lower().strip()
            if norm_domain not in existing:
                obj = OfficialDomain(
                    domain=norm_domain,
                    entity_name=item["entity_name"],
                    entity_type=item["entity_type"],
                    verified_owner=item["verified_owner"],
                    quarterly_review_at=review_date,
                    is_active=True,
                )
                session.add(obj)
                inserted += 1

        if inserted > 0:
            await session.commit()
        return inserted

    @staticmethod
    def seed_default_domains_sync(session: Session) -> int:
        """Synchronously seeds initial verified UAE domains if not already present."""
        existing = AllowlistRepository.get_active_domain_names_sync(session)
        inserted = 0
        review_date = get_default_quarterly_review()

        for item in OFFICIAL_UAE_DOMAINS_SEED:
            norm_domain = item["domain"].lower().strip()
            if norm_domain not in existing:
                obj = OfficialDomain(
                    domain=norm_domain,
                    entity_name=item["entity_name"],
                    entity_type=item["entity_type"],
                    verified_owner=item["verified_owner"],
                    quarterly_review_at=review_date,
                    is_active=True,
                )
                session.add(obj)
                inserted += 1

        if inserted > 0:
            session.commit()
        return inserted
