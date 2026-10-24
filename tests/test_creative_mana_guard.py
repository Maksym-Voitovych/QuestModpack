"""Execute the real component filter/pool policy in a modeled Minecraft host."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CreativeManaGuardTest(unittest.TestCase):
    def test_exact_native_sources_match_all_intercepted_supply_paths(self):
        audit = json.loads((ROOT/'content/audit/v5-creative-mana-guard.json').read_text())
        sources = {}
        for source in audit['sources']:
            data = (ROOT/source['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),source['sha256'])
            sources[Path(source['path']).name] = data.decode()
        self.assertIn('mod_version=1.0.2',sources['gradle.properties'].replace(' ',''))
        handler = sources['ManaItemHandlerImpl.java']
        self.assertIn('public List<ItemStack> getManaItems(Player player)',handler)
        self.assertIn('public List<ItemStack> getManaAccesories(Player player)',handler)
        self.assertGreaterEqual(handler.count('getManaItems(player)'),4)
        self.assertGreaterEqual(handler.count('getManaAccesories(player)'),4)
        self.assertIn('fireManaItemEvent(player, toReturn)',handler)
        self.assertIn('canReceiveManaFromPool(self)',sources['ManaPoolBlockEntity.java'])
        self.assertIn('canExportManaToPool(self)',sources['ManaPoolBlockEntity.java'])
        for method in ['canReceiveManaFromPool','canExportManaToPool']:
            self.assertIn('public boolean '+method+'(BlockEntity pool)',sources['ManaTabletItem.java'])

    def test_live_authority_and_native_output_checks_cannot_use_only_base_item_id(self):
        source = (ROOT/'companion/src/main/java/ua/aia2/guard/Aia2MachineGuard.java').read_text()
        self.assertIn('CreativeManaGuard.isCreativeTablet(output) && !mayUsePostgameMana(player)',source)
        self.assertIn('CreativeManaGuard.mayExchangeWithPool(blockEntity, output)',source)
        method = source.split('public static boolean mayUsePostgameMana(Player player)',1)[1].split('\n    }',1)[0]
        self.assertIn('player instanceof FakePlayer',method)
        self.assertIn('LIVE_TEAMS.resolve(player.getUUID())',method)
        self.assertIn('synchronizedTeam.equals(currentTeam)',method)
        self.assertIn('RECIPE_POLICY.mayUseStage(99, currentTeam)',method)

    def test_real_component_filter_and_pool_guard_with_real_stage_policy(self):
        jdk = Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file(): self.skipTest('External JDK21 unavailable')
        fixtures = {
            'net/minecraft/resources/ResourceLocation.java': '''package net.minecraft.resources;
                public record ResourceLocation(String namespace,String path) {
                  public static ResourceLocation fromNamespaceAndPath(String n,String p){return new ResourceLocation(n,p);}
                }''',
            'net/minecraft/core/component/DataComponents.java': '''package net.minecraft.core.component;
                public final class DataComponents {public static final Object CUSTOM_DATA=new Object();}''',
            'net/minecraft/world/item/component/CustomData.java': '''package net.minecraft.world.item.component;
                public record CustomData(Object creative) {
                  public static final CustomData EMPTY=new CustomData(null);
                  public CustomData copyTag(){return this;}
                  public boolean getBoolean(String key){return Boolean.TRUE.equals(creative)||creative instanceof Number n&&n.intValue()==1;}
                }''',
            'net/minecraft/world/item/ItemStack.java': '''package net.minecraft.world.item;
                import net.minecraft.resources.ResourceLocation; import net.minecraft.world.item.component.CustomData;
                public final class ItemStack {
                  public final ResourceLocation item;public final CustomData data;public int count=1;
                  public ItemStack(String id,Object creative){String[] a=id.split(":");item=new ResourceLocation(a[0],a[1]);data=new CustomData(creative);}
                  public boolean isEmpty(){return count==0;}public ResourceLocation getItem(){return item;}
                  public CustomData getOrDefault(Object type,CustomData fallback){return data;}
                }''',
            'net/minecraft/core/registries/BuiltInRegistries.java': '''package net.minecraft.core.registries;
                import net.minecraft.resources.ResourceLocation;
                public final class BuiltInRegistries {public static final Registry ITEM=new Registry();public static final class Registry {
                  public ResourceLocation getKey(ResourceLocation item){return item;}
                }}''',
            'net/minecraft/world/level/Level.java': '''package net.minecraft.world.level;
                public class Level {private final boolean client;public Level(boolean c){client=c;}public boolean isClientSide(){return client;}}''',
            'net/minecraft/server/level/ServerLevel.java': '''package net.minecraft.server.level;
                public final class ServerLevel extends net.minecraft.world.level.Level {public ServerLevel(){super(false);}}''',
            'net/minecraft/world/entity/player/Player.java': '''package net.minecraft.world.entity.player;
                public final class Player {public String team="a",synced="a";public boolean fake;public final net.minecraft.world.level.Level level;
                  public Player(net.minecraft.world.level.Level l){level=l;}}
                ''',
            'net/minecraft/world/level/block/entity/BlockEntity.java': '''package net.minecraft.world.level.block.entity;
                public final class BlockEntity {public String team="a";private final net.minecraft.world.level.Level level;
                  public BlockEntity(net.minecraft.world.level.Level l){level=l;}public net.minecraft.world.level.Level getLevel(){return level;}}
                ''',
            'ua/aia2/guard/Aia2MachineGuard.java': '''package ua.aia2.guard;
                import net.minecraft.world.entity.player.Player;import net.minecraft.world.level.block.entity.BlockEntity;
                public final class Aia2MachineGuard {
                  public static final GuardPolicy policy=new GuardPolicy();
                  public static boolean mayUsePostgameMana(Player p){return p!=null&&(p.level.isClientSide()||!p.fake&&p.team!=null&&p.team.equals(p.synced)&&policy.mayUseStage(99,p.team));}
                  public static String getOwner(BlockEntity pool){return pool.team;}
                  public static boolean mayObserveStage(String team,int stage){return policy.mayUseStage(stage,team);}
                }''',
            'ua/aia2/guard/CreativeManaHarness.java': '''package ua.aia2.guard;
                import java.util.List; import net.minecraft.world.item.ItemStack;
                import net.minecraft.server.level.ServerLevel;import net.minecraft.world.level.Level;
                import net.minecraft.world.entity.player.Player;import net.minecraft.world.level.block.entity.BlockEntity;
                public final class CreativeManaHarness {
                  static int assertions;static void check(boolean condition,String message){assertions++;if(!condition)throw new AssertionError(message);}
                  public static void main(String[] args){
                    var policy=Aia2MachineGuard.policy;policy.setRules(java.util.Map.of("aia2:postgame",99));policy.setTeamProgress("a",47);policy.setReady();
                    var normal=new ItemStack("botania:mana_tablet",false);var creative=new ItemStack("botania:mana_tablet",1);
                    var other=new ItemStack("minecraft:stone",true);var player=new Player(new ServerLevel());var pool=new BlockEntity(player.level);
                    check(!CreativeManaGuard.isCreativeTablet(normal),"ordinary tablet is finite");
                    check(CreativeManaGuard.isCreativeTablet(creative),"numeric native flag is creative");
                    check(CreativeManaGuard.isCreativeTablet(new ItemStack("botania:mana_tablet",true)),"boolean flag also creative");
                    check(!CreativeManaGuard.isCreativeTablet(other),"same flag on another item unaffected");
                    var finite=List.of(normal,other);check(CreativeManaGuard.filterPlayerSupplies(player,finite)==finite,"no allocation for ordinary supplies");
                    var supplies=List.of(normal,creative,other,creative);var filtered=CreativeManaGuard.filterPlayerSupplies(player,supplies);
                    check(filtered.equals(finite),"all imported creative stacks filtered");check(filtered.getFirst()==normal,"native stack identity preserved");
                    check(supplies.size()==4&&creative.count==1,"immutable native list and stacks untouched");
                    check(!CreativeManaGuard.mayExchangeWithPool(pool,creative),"dropped creative tablet cannot export or absorb through early pool");
                    check(CreativeManaGuard.mayExchangeWithPool(pool,normal),"finite pool exchange unchanged");
                    pool.team=null;check(!CreativeManaGuard.mayExchangeWithPool(pool,creative),"unowned pool denied");pool.team="a";
                    check(!CreativeManaGuard.mayExchangeWithPool(null,creative),"missing pool denied");
                    check(!CreativeManaGuard.mayExchangeWithPool(new BlockEntity(null),creative),"unloaded pool denied");
                    policy.setTeamProgress("a",48);check(CreativeManaGuard.filterPlayerSupplies(player,supplies)==supplies,"completed48 restores ordinary handler behavior");
                    check(CreativeManaGuard.mayExchangeWithPool(pool,creative),"completed48 permits owned pool");
                    player.fake=true;check(CreativeManaGuard.filterPlayerSupplies(player,supplies).equals(finite),"fake player cannot borrow authority");player.fake=false;
                    player.synced="old-team";check(CreativeManaGuard.filterPlayerSupplies(player,supplies).equals(finite),"stale team projection denied");player.synced="a";
                    policy.setTeamProgress("a",47);check(!CreativeManaGuard.mayExchangeWithPool(pool,creative),"access loss closes existing imported tablet");
                    var client=new Player(new Level(true));check(CreativeManaGuard.filterPlayerSupplies(client,supplies)==supplies,"client presentation unaffected");
                    check(CreativeManaGuard.mayExchangeWithPool(new BlockEntity(client.level),creative),"client pool preview unaffected");
                    check(CreativeManaGuard.filterPlayerSupplies(player,null)==null,"null native supply list preserved");
                    policy.clear();check(!CreativeManaGuard.mayExchangeWithPool(pool,creative),"unready authority closed");
                    System.out.println("CreativeManaHarness: "+assertions+" real-helper/real-policy assertions passed; modeled Minecraft host, no Botania dispatch");
                  }
                }''',
        }
        with tempfile.TemporaryDirectory(prefix='aia2-creative-mana-') as directory:
            files=[]
            for name,text in fixtures.items():
                path=Path(directory)/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);files.append(str(path))
            files += [str(ROOT/'companion/src/main/java/ua/aia2/guard/CreativeManaGuard.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/GuardPolicy.java')]
            result=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-d',directory,*files],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(jdk/'bin/java'),'-cp',directory,'ua.aia2.guard.CreativeManaHarness'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('22 real-helper/real-policy assertions passed',result.stdout)
            print(result.stdout.strip())
