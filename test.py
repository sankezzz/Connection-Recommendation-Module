
import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect(

        "postgresql://postgres.wnkjqmdoosbtukjbzknu:H2f_i9dYWDWj8ds@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
    )
    print("Connected!")
    await conn.close()

asyncio.run(test())