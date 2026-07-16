from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.customers.models import Customer
from app.customers.schemas import CustomerCreate, CustomerUpdate
from app.leads.models import Lead, LeadStatus
from app.core.exceptions import NotFoundError, ConflictError


# Create a new customer.
# Rolls back the transaction if the email already exists.
async def create_customer(db: AsyncSession, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    try:
        await db.commit()
        await db.refresh(customer)
        return customer
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Customer with this email already exists.")


# Return a paginated list of customers with optional filters.
async def list_customers(db: AsyncSession, skip: int, limit: int, filters: dict):
    stmt = select(Customer)

    # Apply filters only when provided by the client.
    if filters.get("name"):
        stmt = stmt.where(Customer.name.ilike(f"%{filters['name']}%")) #Partial text match (e.g., searching "zun" finds "Zunaira").

    if filters.get("email"):
        stmt = stmt.where(Customer.email.ilike(f"%{filters['email']}%"))

    if filters.get("phone"):
        stmt = stmt.where(Customer.phone.ilike(f"%{filters['phone']}%"))

    if filters.get("created_after"):
        stmt = stmt.where(Customer.created_at >= filters["created_after"])

    if filters.get("created_before"):
        stmt = stmt.where(Customer.created_at <= filters["created_before"])
    # Inside the list_customers function, add this block:
    if filters.get("has_active_leads") is not None:
        active_statuses = [LeadStatus.new, LeadStatus.contacted, LeadStatus.qualified, LeadStatus.viewing, LeadStatus.offered]
    if filters["has_active_leads"]:
            # Returns customers who have AT LEAST ONE active lead
        stmt = stmt.where(Customer.leads.any(Lead.status.in_(active_statuses)))
    else:
            # Returns customers who have NO active leads
        stmt = stmt.where(~Customer.leads.any(Lead.status.in_(active_statuses)))

    # Count the total number of matching records before pagination.
    total = await db.scalar(
        select(func.count()).select_from(stmt.subquery())
    )

    # Return only the requested page of results.
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)

    return total, result.scalars().all()


# Retrieve a customer by ID.
# Raise a domain-specific exception if the customer does not exist.
async def get_customer(db: AsyncSession, customer_id: UUID) -> Customer:
    customer = await db.scalar(
        select(Customer).where(Customer.id == customer_id)
    )

    if not customer:
        raise NotFoundError("Customer not found")

    return customer


# Update only the fields provided by the client.
async def update_customer(
    db: AsyncSession,
    customer_id: UUID,
    data: CustomerUpdate
) -> Customer:

    customer = await get_customer(db, customer_id)

    # Ignore fields that were not supplied in the request.
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(customer, key, value)

    try:
        await db.commit()
        await db.refresh(customer)
        return customer

    except IntegrityError:
        await db.rollback()
        raise ConflictError("Customer with this email already exists.")


# Delete a customer.
# Optionally prevent deletion if the customer has active leads.
async def delete_customer(
    db: AsyncSession,
    customer_id: UUID,
    enforce_guard: bool
):

    # Business rule: customers with active leads cannot be deleted.
    if enforce_guard:

        active_statuses = [
            LeadStatus.new,
            LeadStatus.contacted,
            LeadStatus.qualified
        ]

        active_leads = await db.scalar(
            select(func.count()).select_from(Lead).where(
                Lead.customer_id == customer_id,
                Lead.status.in_(active_statuses)
            )
        )

        if active_leads > 0:
            raise ConflictError(
                f"Cannot delete. Customer has {active_leads} active leads."
            )

    customer = await get_customer(db, customer_id)

    try:
        await db.delete(customer)
        await db.commit()

    except IntegrityError:
        await db.rollback()

        # Database-level constraint prevents deleting customers that are
        # still referenced by related records.
        raise ConflictError(
            "Cannot delete customer with terminal leads attached."
        )