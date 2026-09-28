"""首次启动的种子食谱数据（常见家常菜，营养为估算值/份）"""
from sqlalchemy import func

from .database import Recipe, SessionLocal, Setting

SEED_FLAG_KEY = "seeded"

SEED_RECIPES = [
    {
        "name": "番茄炒蛋", "category": "家常菜", "cuisine": "家常",
        "description": "国民下饭菜，酸甜开胃。",
        "ingredients": [{"name": "番茄", "amount": "2个"}, {"name": "鸡蛋", "amount": "3个"}, {"name": "葱花", "amount": "少许"}, {"name": "盐/糖", "amount": "适量"}],
        "steps": ["鸡蛋打散加少许盐", "热油炒蛋至凝固盛出", "番茄切块下锅炒出汁", "倒回鸡蛋，加盐糖调味", "撒葱花出锅"],
        "calories": 180, "protein": 9, "fat": 11, "carbs": 9, "tags": ["快手菜", "下饭"],
    },
    {
        "name": "青椒肉丝", "category": "荤菜", "cuisine": "川菜",
        "description": "咸香微辣的经典小炒。",
        "ingredients": [{"name": "猪里脊", "amount": "200g"}, {"name": "青椒", "amount": "2个"}, {"name": "蒜末", "amount": "适量"}, {"name": "生抽/淀粉", "amount": "适量"}],
        "steps": ["肉丝用生抽淀粉抓匀腌10分钟", "热油滑炒肉丝至变色盛出", "爆香蒜末，下青椒丝", "倒回肉丝大火翻炒", "调味出锅"],
        "calories": 260, "protein": 22, "fat": 14, "carbs": 8, "tags": ["下饭", "快手菜"],
    },
    {
        "name": "麻婆豆腐", "category": "素菜", "cuisine": "川菜",
        "description": "麻辣鲜香，豆腐嫩滑。",
        "ingredients": [{"name": "嫩豆腐", "amount": "1盒"}, {"name": "猪肉末", "amount": "80g"}, {"name": "豆瓣酱", "amount": "1勺"}, {"name": "花椒粉", "amount": "少许"}],
        "steps": ["豆腐切块焯水", "炒肉末至酥香", "下豆瓣酱炒出红油", "加水下豆腐轻推入味", "勾芡撒花椒粉葱花"],
        "calories": 210, "protein": 14, "fat": 13, "carbs": 8, "tags": ["下饭", "川菜"],
    },
    {
        "name": "清炒西兰花", "category": "素菜", "cuisine": "家常",
        "description": "简单健康，保留蔬菜清甜。",
        "ingredients": [{"name": "西兰花", "amount": "300g"}, {"name": "蒜末", "amount": "3瓣"}, {"name": "盐", "amount": "适量"}],
        "steps": ["西兰花掰小朵焯水1分钟", "热油爆香蒜末", "大火快炒西兰花", "盐调味出锅"],
        "calories": 85, "protein": 6, "fat": 4, "carbs": 8, "tags": ["低卡", "健康"],
    },
    {
        "name": "紫菜蛋花汤", "category": "汤羹", "cuisine": "家常",
        "description": "五分钟快手汤。",
        "ingredients": [{"name": "紫菜", "amount": "1小块"}, {"name": "鸡蛋", "amount": "1个"}, {"name": "香油/盐", "amount": "适量"}],
        "steps": ["水开下紫菜", "淋入蛋液成蛋花", "盐和香油调味"],
        "calories": 70, "protein": 5, "fat": 4, "carbs": 3, "tags": ["快手菜", "汤"],
    },
    {
        "name": "可乐鸡翅", "category": "荤菜", "cuisine": "家常",
        "description": "甜咸适口，小朋友最爱。",
        "ingredients": [{"name": "鸡翅中", "amount": "8个"}, {"name": "可乐", "amount": "1罐"}, {"name": "生抽/姜片", "amount": "适量"}],
        "steps": ["鸡翅划刀焯水", "煎至两面金黄", "倒入可乐和生抽", "中火收汁"],
        "calories": 320, "protein": 20, "fat": 15, "carbs": 22, "tags": ["孩子爱吃"],
    },
    {
        "name": "红烧排骨", "category": "荤菜", "cuisine": "家常",
        "description": "浓油赤酱，软烂入味。",
        "ingredients": [{"name": "猪肋排", "amount": "500g"}, {"name": "冰糖", "amount": "20g"}, {"name": "生抽/老抽/料酒", "amount": "适量"}, {"name": "姜葱", "amount": "适量"}],
        "steps": ["排骨焯水去沫", "冰糖炒糖色", "下排骨翻炒上色", "加水和调料小火炖40分钟", "大火收汁"],
        "calories": 420, "protein": 25, "fat": 30, "carbs": 10, "tags": ["硬菜"],
    },
    {
        "name": "水蒸蛋", "category": "家常菜", "cuisine": "家常",
        "description": "嫩滑如布丁的蒸蛋。",
        "ingredients": [{"name": "鸡蛋", "amount": "2个"}, {"name": "温水", "amount": "150ml"}, {"name": "香油/生抽", "amount": "几滴"}],
        "steps": ["蛋液加1.5倍温水打匀过筛", "盖保鲜膜扎孔", "水开后中火蒸10分钟", "淋香油生抽"],
        "calories": 140, "protein": 11, "fat": 9, "carbs": 2, "tags": ["孩子爱吃", "蒸蛋"],
    },
    {
        "name": "白灼虾", "category": "荤菜", "cuisine": "粤菜",
        "description": "原汁原味，高蛋白低脂。",
        "ingredients": [{"name": "鲜虾", "amount": "300g"}, {"name": "姜片/料酒", "amount": "适量"}, {"name": "蒸鱼豉油", "amount": "蘸食"}],
        "steps": ["水开加姜和料酒", "下虾煮2分钟至变红", "捞出过冰水", "蘸豉油食用"],
        "calories": 120, "protein": 20, "fat": 2, "carbs": 1, "tags": ["高蛋白", "低卡"],
    },
    {
        "name": "凉拌黄瓜", "category": "素菜", "cuisine": "家常",
        "description": "清爽解腻小凉菜。",
        "ingredients": [{"name": "黄瓜", "amount": "2根"}, {"name": "蒜末", "amount": "3瓣"}, {"name": "醋/糖/香油", "amount": "适量"}],
        "steps": ["黄瓜拍裂切段", "加盐腌10分钟沥水", "加蒜末醋糖香油拌匀"],
        "calories": 50, "protein": 2, "fat": 2, "carbs": 7, "tags": ["低卡", "凉菜"],
    },
    {
        "name": "小米粥", "category": "汤羹", "cuisine": "家常",
        "description": "养胃粥品首选。",
        "ingredients": [{"name": "小米", "amount": "80g"}, {"name": "水", "amount": "1L"}],
        "steps": ["小米淘洗", "水开下米", "小火熬25分钟至浓稠"],
        "calories": 150, "protein": 4, "fat": 1.5, "carbs": 30, "tags": ["养胃", "清淡"],
    },
    {
        "name": "燕麦牛奶", "category": "汤羹", "cuisine": "西式",
        "description": "三分钟快手营养餐。",
        "ingredients": [{"name": "即食燕麦", "amount": "40g"}, {"name": "牛奶", "amount": "250ml"}, {"name": "坚果/水果", "amount": "随意"}],
        "steps": ["牛奶加热", "冲入燕麦焖2分钟", "撒坚果水果"],
        "calories": 220, "protein": 10, "fat": 8, "carbs": 28, "tags": ["快手菜", "健康"],
    },
    {
        "name": "土豆炖牛肉", "category": "荤菜", "cuisine": "家常",
        "description": "土豆软糯牛肉酥烂。",
        "ingredients": [{"name": "牛腩", "amount": "400g"}, {"name": "土豆", "amount": "2个"}, {"name": "八角/生抽/老抽", "amount": "适量"}],
        "steps": ["牛腩焯水", "炒香调料下牛肉", "加水炖1小时", "下土豆再炖20分钟", "收汁"],
        "calories": 380, "protein": 26, "fat": 18, "carbs": 26, "tags": ["硬菜", "炖菜"],
    },
    {
        "name": "蒜蓉油麦菜", "category": "素菜", "cuisine": "家常",
        "description": "清脆碧绿的快手绿叶菜。",
        "ingredients": [{"name": "油麦菜", "amount": "300g"}, {"name": "蒜末", "amount": "4瓣"}, {"name": "盐/蚝油", "amount": "适量"}],
        "steps": ["热油爆香蒜末", "大火下油麦菜快炒", "盐和蚝油调味"],
        "calories": 70, "protein": 2, "fat": 4, "carbs": 6, "tags": ["低卡", "快手菜"],
    },
    {
        "name": "冬瓜排骨汤", "category": "汤羹", "cuisine": "家常",
        "description": "清热去火的家常汤。",
        "ingredients": [{"name": "排骨", "amount": "300g"}, {"name": "冬瓜", "amount": "400g"}, {"name": "姜片/盐", "amount": "适量"}],
        "steps": ["排骨焯水", "加水姜片炖40分钟", "下冬瓜煮15分钟", "盐调味"],
        "calories": 190, "protein": 15, "fat": 10, "carbs": 7, "tags": ["汤", "清热"],
    },
    {
        "name": "鸡蛋灌饼", "category": "家常菜", "cuisine": "面食",
        "description": "外酥里嫩的鸡蛋饼。",
        "ingredients": [{"name": "面粉", "amount": "150g"}, {"name": "鸡蛋", "amount": "1个"}, {"name": "生菜/甜面酱", "amount": "适量"}],
        "steps": ["和面醒20分钟", "擀薄刷油卷起再擀", "烙至起泡灌入蛋液", "刷酱卷生菜"],
        "calories": 320, "protein": 11, "fat": 10, "carbs": 45, "tags": ["面食"],
    },
    {
        "name": "宫保鸡丁", "category": "荤菜", "cuisine": "川菜",
        "description": "酸甜微辣，花生香脆。",
        "ingredients": [{"name": "鸡胸肉", "amount": "250g"}, {"name": "花生米", "amount": "50g"}, {"name": "干辣椒/花椒", "amount": "适量"}, {"name": "糖醋生抽", "amount": "调汁"}],
        "steps": ["鸡丁腌制", "调碗汁", "炒香干辣椒花椒", "下鸡丁炒熟", "倒入碗汁加花生"],
        "calories": 300, "protein": 28, "fat": 14, "carbs": 12, "tags": ["下饭", "高蛋白"],
    },
    {
        "name": "蒜蓉粉丝蒸娃娃菜", "category": "素菜", "cuisine": "家常",
        "description": "清淡鲜美的蒸菜。",
        "ingredients": [{"name": "娃娃菜", "amount": "2棵"}, {"name": "粉丝", "amount": "1把"}, {"name": "蒜蓉", "amount": "1头"}, {"name": "蒸鱼豉油", "amount": "适量"}],
        "steps": ["粉丝泡软垫底", "娃娃菜切块铺上", "炒香蒜蓉铺面", "蒸8分钟淋豉油"],
        "calories": 120, "protein": 3, "fat": 3, "carbs": 20, "tags": ["蒸菜", "清淡"],
    },
]


def seed_if_empty() -> None:
    # 写过一次标记后就不再 seed：用户清空菜谱后，重启不会把演示数据带回来
    with SessionLocal() as db:
        if db.get(Setting, SEED_FLAG_KEY):
            return
        count = db.query(func.count(Recipe.id)).scalar()
        if count:
            db.add(Setting(key=SEED_FLAG_KEY, value_text='{"done": true}'))
            db.commit()
            return
        for r in SEED_RECIPES:
            recipe = Recipe(
                name=r["name"], category=r["category"], cuisine=r["cuisine"],
                description=r["description"], servings=1,
                calories=r["calories"], protein=r["protein"], fat=r["fat"], carbs=r["carbs"],
                is_ai_generated=False,
            )
            recipe.ingredients = r["ingredients"]
            recipe.steps = r["steps"]
            recipe.tags = r["tags"]
            db.add(recipe)
        db.add(Setting(key=SEED_FLAG_KEY, value_text='{"done": true}'))
        db.commit()
