"""
【游戏角色:】
狼人：夜晚击杀好人，白天隐藏身份
预言家：每晚查验一名玩家身份
女巫：拥有解药和毒药各一瓶
猎人：被投票出局时可开枪带走一名玩家
村民：通过推理和投票找出狼人
"""


class GameRole:
    """游戏角色管理类"""
    
    ROLES = {
        "狼人": {
            "description": "狼人",
            "ability": "夜晚可以击杀一名玩家",
            "win_condition": "消灭所有好人或与好人数量相等",
            "team": "狼人阵营"
        },
        "预言家": {
            "description": "预言家",
            "ability": "每晚可以查验一名玩家的身份",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        },
        "女巫": {
            "description": "女巫",
            "ability": "拥有解药和毒药各一瓶，可以救人或杀人",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        },
        "猎人": {
            "description": "猎人",
            "ability": "被投票出局时可以开枪带走一名玩家",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        },
        "村民": {
            "description": "村民",
            "ability": "无特殊技能，依靠推理和投票",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        },
        "守护者": {
            "description": "守护者",
            "ability": "每晚可以守护一名玩家免受狼人攻击",
            "win_condition": "消灭所有狼人",
            "team": "好人阵营"
        }
    }

    @classmethod
    def get_role_desc(cls, role: str) -> str:
        """获取角色描述"""
        return cls.ROLES.get(role, {}).get("description", "未知角色")
    
    @classmethod
    def get_role_ability(cls, role: str) -> str:
        """获取角色技能"""
        return cls.ROLES.get(role, {}).get("ability", "无特殊技能")
    
    @classmethod
    def is_werewolf(cls, role: str) -> bool:
        """判断是否为狼人"""
        return role == "狼人"
    
    @classmethod
    def is_villager_team(cls, role: str) -> bool:
        """判断是否为好人阵营"""
        return cls.ROLES.get(role, {}).get("team") == "好人阵营"
    
    
