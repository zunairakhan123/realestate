from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.customers.models import Customer
from app.customers.schemas import CustomerCreate, CustomerRegisterSchema, CustomerUpdate
from app.auth.models import User, UserRole
from app.core.auth import get_password_hash
from app.leads.models import Lead, LeadStatus
from app.core.exceptions import NotFoundError, ConflictError

# Create a new customer and a corresponding authentication User record simultaneously.
async def create_customer(db: AsyncSession, data: CustomerCreate | CustomerRegisterSchema) -> Customer:
    # 1. Check if a user/customer with this email already exists
    existing_user = await db.scalar(select(User).where(User.email == data.email))
    if existing_user:
        raise ConflictError("A user/customer with this email already exists.")

    # 2. Extract password safely from registration schema or fallback if called internally
    raw_password = getattr(data, "password", None) or "DefaultPassword123!"

    # 3. Create the core authentication User record with role = CUSTOMER
    db_user = User(
        email=data.email,
        hashed_password=get_password_hash(raw_password),
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(db_user)
    await db.flush() # Flush to populate db_user.id

    # 4. Create the Customer profile linked via user_id (excluding password field)
    customer_data = data.model_dump(exclude={"password"}, mode="unset")
    customer = Customer(user_id=db_user.id, **customer_data)
    db.add(customer)

    try:
        await db.commit()
        await db.refresh(customer)
        return customer
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Customer with this email or user association already exists.")


# Return a paginated list of customers with optional filters.
async def list_customers(db: AsyncSession, skip: int, limit: int, filters: dict):
    stmt = select(Customer)

    if filters.get("name"):
        stmt = stmt.where(Customer.name.ilike(f"%{filters['name']}%"))

    if filters.get("email"):
        stmt = stmt.where(Customer.email.ilike(f"%{filters['email']}%"))

    if filters.get("phone"):
        stmt = stmt.where(Customer.phone.ilike(f"%{filters['phone']}%"))

    if filters.get("created_after"):
        stmt = stmt.where(Customer.created_at >= filters["created_after"])

    if filters.get("created_before"):
        stmt = stmt.where(Customer.created_at <= filters["created_before"])

    if filters.get("has_active_leads") is not None:
        active_statuses = [LeadStatus.new, LeadStatus.contacted, LeadStatus.qualified, LeadStatus.viewing, LeadStatus.offered]
        if filters["has_active_leads"]:
            stmt = stmt.where(Customer.leads.any(Lead.status.in_(active_statuses)))
        else:
            stmt = stmt.where(~Customer.leads.any(Lead.status.in_(active_statuses)))

    total = await db.scalar(
        select(func.count()).select_from(stmt.subquery())
    )

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)

    return total or 0, result.scalars().all()


# Retrieve a customer by ID.
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

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(customer, key, value)

    try:
        await db.commit()
        await db.refresh(customer)
        return customer

    except IntegrityError:
        await db.rollback()
        raise ConflictError("Customer update caused an email conflict.")


# Delete a customer.
async def delete_customer(
    db: AsyncSession,
    customer_id: UUID,
    enforce_guard: bool
):
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

        if active_leads and active_leads > 0:
            raise ConflictError(
                f"Cannot delete. Customer has {active_leads} active leads."
            )

    customer = await get_customer(db, customer_id)

    try:
        if customer.user_id:
            user = await db.scalar(select(User).where(User.id == customer.user_id))
            if user:
                await db.delete(user)
        
        await db.delete(customer)
        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise ConflictError(
            "Cannot delete customer with terminal leads attached."
        )