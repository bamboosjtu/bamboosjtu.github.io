from typing import List, Dict, Optional

from agentscope.agent import ReActAgent, AgentBase
from agentscope.pipeline import MsgHub, sequential_pipeline, fanout_pipeline
from agentscope.message import Msg
import asyncio
import sys
import random
from collections import Counter

from players import GameModerator, GamePlayer

from structured_output_cn import (
    DiscussionModelCN,
    WerewolfKillModelCN,
    VoteModelCN,
    SeerModelCN,
    get_seer_model_cn,
    WitchActionModelCN,
    # get_hunter_model_cn,
)


sys.stdout.reconfigure(encoding="utf-8")

MAX_GAME_ROUND = 20
MAX_DISCUSSION_ROUND = 2

def format_player_list(players: List[AgentBase], show_roles: bool = False) -> str:
        """格式化玩家列表为中文显示"""
        if not players:
            return "无玩家"
        
        if show_roles:
            return "、".join([f"{p.name}({getattr(p, 'role', '未知')})" for p in players])
        else:
            return "、".join([p.name for p in players])


def majority_vote_cn(votes: Dict[str, str]) -> tuple[str, int]:
    """中文版多数投票统计"""
    if not votes:
        return "无人", 0
    
    vote_counts = Counter(votes.values())
    print(f"😀 本次投票结果：{vote_counts}。")
    most_voted = vote_counts.most_common(1)[0]
    
    return most_voted[0], most_voted[1]

def pretty_msg(msg: Msg):
    lines = []

    # 角色名
    lines.append(f"[{msg.name}]-[{msg.role}]")

    # 最终发言（text block）
    for block in msg.content:
        lines.append(f"[{block["type"]}]{block[block["type"]]}")

    # 结构化结果（metadata）
    if msg.metadata:
        lines.append("[决策结果]")
        for k, v in msg.metadata.items():
            lines.append(f"  - {k}: {v}")

    return "\n".join(lines)

class ThreeKingdomsWerewolfGame:
    """三国狼人杀游戏主类"""

    def __init__(self):
        self.players: Dict[str, ReActAgent] = {}
        self.roles: Dict[str, str] = {}
        self.moderator = GameModerator()
        self.alive_players: List[ReActAgent] = []
        self.werewolves: List[ReActAgent] = []
        self.villagers: List[ReActAgent] = []
        self.seer: List[ReActAgent] = []
        self.witch: List[ReActAgent] = []
        self.hunter: List[ReActAgent] = []
        
        # 女巫道具状态
        self.witch_has_antidote = True
        self.witch_has_poison = True
    

    async def setup_game(self, player_count: int = 6):
        """设置游戏"""
        print("🎮 开始设置三国狼人杀游戏...")

        # 获取角色配置
        roles = ["狼人", "狼人", "预言家", "女巫", "村民", "村民"]
        characters = random.sample(GamePlayer.CHINESE_NAMES, 6)
        print(f'本次参与游戏的玩家有：{characters}。')
        
        wolf_names = []
        # 创建玩家
        for i, (role, character) in enumerate(zip(roles, characters)):
            agent = await GamePlayer.create_player(character, role, self.moderator)
            self.alive_players.append(agent)
            
            # 分配到对应阵营
            if role == "狼人":
                self.werewolves.append(agent)
                wolf_names.append(character)
            elif role == "预言家":
                self.seer.append(agent)
            elif role == "女巫":
                self.witch.append(agent)
            elif role == "猎人":
                self.hunter.append(agent)
            else:
                self.villagers.append(agent)
        
        # 游戏开始公告
        await self.moderator.announce(
            f"三国狼人杀游戏开始！参与者：{format_player_list(self.alive_players)}"
        )

        for wolf in self.werewolves:
            await wolf.observe(
                await self.moderator.announce(
                    f"狼人阵营{'、'.join(wolf_names)}相互确认队友。"
                )
        )
        
        print(f"✅ 游戏设置完成，共{len(self.alive_players)}名玩家")


    async def werewolf_phase(self, round_num: int):
        """狼人阶段"""
        if not self.werewolves:
            return None
            
        await self.moderator.announce(f"🐺 狼人请睁眼...")
        
        # 狼人讨论
        async with MsgHub(
            self.werewolves,
            enable_auto_broadcast=True,
            announcement=await self.moderator.announce(
                f"狼人们，场上存活玩家：{format_player_list(self.alive_players)}，请讨论今晚的击杀目标。"
            ),
        ) as werewolves_hub:
            # 讨论阶段
            for _ in range(MAX_DISCUSSION_ROUND):
                for wolf in self.werewolves:
                    res = await wolf(structured_model=DiscussionModelCN)
                    wolf.logger.debug(
                        f"[Round {round_num}][Night][Discussion] "
                        f"[Msg] {pretty_msg(res)}。 "
                    )
                    print(f"😀 {wolf.name}的决策{res.metadata}")
                    await asyncio.sleep(10)
            
            # 投票击杀
            werewolves_hub.set_auto_broadcast(False)
            await self.moderator.announce("狼人们，讨论结束，下一步投票选择今晚的击杀目标...")

            kill_votes = await fanout_pipeline(
                self.werewolves,
                msg=await self.moderator.announce("请选择击杀目标"),
                structured_model=WerewolfKillModelCN,
                enable_gather=False,
            )
            await asyncio.sleep(10)
            print(f"😀 击杀投票结果:")
            for _ in kill_votes:
                agent = [ag for ag in self.werewolves if ag.name == _.name][0]
                agent.logger.debug(
                        f"[Round {round_num}][Night][Kill] "
                        f"[Msg] {pretty_msg(_)}。 "
                    )
                print(f'\t-{str(_.metadata)}')            

            # 统计投票
            votes = {}
            for i, vote_msg in enumerate(kill_votes):
                # 检查vote_msg是否为None或metadata是否存在
                if vote_msg is not None and hasattr(vote_msg, 'metadata') and vote_msg.metadata is not None:
                    votes[self.werewolves[i].name] = vote_msg.metadata.get("target")
                else:
                    # 如果返回无效,随机选择一个目标
                    print(f"⚠️ {self.werewolves[i].name} 的击杀投票无效,随机选择目标")
                    import random
                    valid_targets = [p.name for p in self.alive_players if p.name not in [w.name for w in self.werewolves]]
                    votes[self.werewolves[i].name] = random.choice(valid_targets) if valid_targets else None
            
            killed_player, _ = majority_vote_cn(votes)
            await self.moderator.announce(f"狼人们，今晚你们击杀{killed_player}...")
            await asyncio.sleep(10)
            return killed_player
        

    async def seer_phase(self, round_num: int):
        """预言家阶段"""
        if not self.seer:
            return
            
        seer_agent = self.seer[0]
        valid_names = {p.name for p in self.alive_players}
        await self.moderator.announce(f"🔮 预言家请睁眼，请从{"、".join(valid_names)}中,选择要查验的对象...")
        
        check_result = await seer_agent(
            structured_model=get_seer_model_cn(self.alive_players)
        )
        seer_agent.logger.debug(
            f"[Round {round_num}][Night][预言家查验] "
            f"[Msg] {pretty_msg(check_result)}。 "
            )
        print(f"😀 预言家查验: {check_result.metadata}")

        # 检查返回结果是否有效
        if check_result is None or not hasattr(check_result, 'metadata') or check_result.metadata is None:
            print(f"⚠️ 预言家查验失败,跳过此阶段")
            return
        target_name = check_result.metadata.get("target")
        if not target_name:
            print(f"⚠️ 预言家未选择查验目标,跳过此阶段")
            return

        # 告知预言家结果
        wolf_names = {p.name for p in self.werewolves}
        result_msg = f"查验结果：{target_name}是{'狼人' if target_name in wolf_names else '好人'}"
        await seer_agent.observe(await self.moderator.announce(result_msg))


    async def witch_phase(self, killed_player: str, round_num: int):
        """女巫阶段"""
        if not self.witch:
            return killed_player, None
            
        witch_agent = self.witch[0]
        await self.moderator.announce("🧙‍♀️ 女巫请睁眼...")

        if not self.witch_has_antidote and not self.witch_has_poison:
            return killed_player, None
        
        # 告知女巫死亡信息
        valid_names = {p.name for p in self.alive_players}
        death_info = f"今晚{killed_player}被狼人击杀" if killed_player else "今晚平安无事" 
        death_info = death_info + "，你可以使用解药。" if self.witch_has_antidote else "你的解药已经用完。"
        poison_info = f"场上有这些玩家{"、".join(valid_names)}，你可以使用毒药。" if self.witch_has_poison else "你的毒药已经用完"
        await witch_agent.observe(await self.moderator.announce(death_info))
        await witch_agent.observe(await self.moderator.announce(poison_info))

        # 女巫行动
        witch_action = await witch_agent(structured_model=WitchActionModelCN)
        witch_agent.logger.debug(
            f"[Round {round_num}][Night][女巫行动] "
            f"[Msg] {pretty_msg(witch_action)}。 "
            )
        print(f"😀 女巫行动: {witch_action.metadata}")

        saved_player = None
        poisoned_player = None

        # 检查返回结果是否有效
        if witch_action is None or not hasattr(witch_action, 'metadata') or witch_action.metadata is None:
            print(f"⚠️ 女巫行动失败,视为不使用技能")
        else:
            if witch_action.metadata.get("use_antidote") and self.witch_has_antidote:
                if killed_player:
                    saved_player = killed_player
                    self.witch_has_antidote = False
                    await witch_agent.observe(await self.moderator.announce(f"你使用解药救了{killed_player}"))

            elif witch_action.metadata.get("use_poison") and self.witch_has_poison:
                poisoned_player = witch_action.metadata.get("target_name")
                if poisoned_player in valid_names:
                    self.witch_has_poison = False
                    await witch_agent.observe(await self.moderator.announce(f"你使用毒药毒杀了{poisoned_player}"))
                else:
                    # 非法目标，视为不使用毒药（或要求重试）
                    poisoned_player = None
                    self.witch_has_poison = False
        
        # 确定最终死亡玩家
        final_killed = killed_player if not saved_player else None
        
        return final_killed, poisoned_player
    
    async def day_phase(self, round_num: int):
        """白天阶段"""
        await self.moderator.day_announcement(round_num)
        random.shuffle(self.alive_players)
        # 讨论阶段
        async with MsgHub(
            self.alive_players,
            enable_auto_broadcast=True,
            announcement=await self.moderator.announce(
                f"现在开始顺序发言讨论。存活玩家：{format_player_list(self.alive_players)}"
            ),
        ) as all_hub:
            # 每人发言一次
            # await sequential_pipeline(self.alive_players)
            for player in self.alive_players:
                res = await player(structured_model=DiscussionModelCN)
                player.logger.debug(
                    f"[Round {round_num}][Day][Discuss] "
                    f"[Msg] {pretty_msg(res)}。 "
                    )
                print(f"😀 {player.name}白天发言: {res.metadata}")
                await asyncio.sleep(5)  # 可选，防限速

            # 投票阶段
            # all_hub.set_auto_broadcast(False)
            vote_msgs = await fanout_pipeline(
                self.alive_players,
                await self.moderator.announce("请投票选择要淘汰的玩家"),
                structured_model=VoteModelCN,
                enable_gather=False,
            )
            print(f"😀 白天投票情况: ")
            for _ in vote_msgs:
                agent = [ag for ag in self.alive_players if ag.name == _.name][0]
                agent.logger.debug(
                        f"[Round {round_num}][Day][Vote] "
                        f"[Msg] {pretty_msg(_)}。 "
                    )
                print(f'\t-{str(_.metadata)}')  
            
            # 统计投票
            votes = {}
            for i, vote_msg in enumerate(vote_msgs):
                # 检查vote_msg是否为None或metadata是否存在
                if vote_msg is not None and hasattr(vote_msg, 'metadata') and vote_msg.metadata is not None:
                    votes[self.alive_players[i].name] = vote_msg.metadata.get("vote")
                else:
                    # 如果返回无效,默认弃票
                    print(f"⚠️ {self.alive_players[i].name} 的投票无效,视为弃票")
                    votes[self.alive_players[i].name] = None
            
            voted_out, vote_count = majority_vote_cn(votes)
            await self.moderator.vote_result_announcement(voted_out, vote_count)
            return voted_out
    

    def update_alive_players(self, dead_players: List[str]):
        """更新存活玩家列表"""
        for dead_name in dead_players:
            if dead_name:
                # 从存活列表移除
                self.alive_players = [p for p in self.alive_players if p.name != dead_name]
                # 从各阵营移除
                self.werewolves = [p for p in self.werewolves if p.name != dead_name]
                self.villagers = [p for p in self.villagers if p.name != dead_name]
                self.seer = [p for p in self.seer if p.name != dead_name]
                self.witch = [p for p in self.witch if p.name != dead_name]
                self.hunter = [p for p in self.hunter if p.name != dead_name]


    def check_winning_cn(self) -> Optional[str]:
        """检查中文版游戏胜利条件"""
        werewolf_count = len(self.werewolves)
        villager_count = len(self.alive_players) - werewolf_count
        
        if werewolf_count == 0:
            return "好人阵营胜利！所有狼人已被淘汰！"
        elif werewolf_count >= villager_count:
            return "狼人阵营胜利！狼人数量已达到或超过好人！"
        
        return None


    async def run_game(self):
        """运行游戏主循环"""
        try:
            await self.setup_game()
            
            for round_num in range(1, MAX_GAME_ROUND + 1):
                print(f"\n🌙 === 第{round_num}轮游戏开始 ===")
                
                # 夜晚阶段
                await self.moderator.night_announcement(round_num)
                
                # 狼人击杀
                killed_player = await self.werewolf_phase(round_num)

                # 预言家查验
                await self.seer_phase(round_num)

                # 女巫行动
                final_killed, poisoned_player = await self.witch_phase(killed_player, round_num)

                # 更新死亡玩家
                night_deaths = [p for p in [final_killed, poisoned_player] if p]
                self.update_alive_players(night_deaths)
  
                # 死亡公告
                await self.moderator.death_announcement(night_deaths)

                # 检查胜利条件
                winner = self.check_winning_cn()
                if winner:
                    await self.moderator.game_over_announcement(winner)
                    return

                # 白天阶段
                voted_out = await self.day_phase(round_num)

                # 猎人技能
                # hunter_shot = await self.hunter_phase(voted_out)

                # 更新死亡玩家
                day_deaths = [p for p in [voted_out] if p] #, hunter_shot
                self.update_alive_players(day_deaths)

                # 检查胜利条件
                winner = self.check_winning_cn()
                if winner:
                    await self.moderator.game_over_announcement(winner)
                    return
                
                print(f"第{round_num}轮结束，存活玩家：{format_player_list(self.alive_players)}")
                
        
        except Exception as e:
            print(f"❌ 游戏运行出错：{e}")
            import traceback
            traceback.print_exc()




async def main():
    """主函数"""
    import warnings
    warnings.filterwarnings('ignore')
    import agentscope
    agentscope.init(logging_level="CRITICAL")
    
    print("🎮 欢迎来到三国狼人杀！")
    
    # 创建并运行游戏
    game = ThreeKingdomsWerewolfGame()
    await game.run_game()


if __name__ == "__main__":
    asyncio.run(main())