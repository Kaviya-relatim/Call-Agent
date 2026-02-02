import asyncio
from livekit import api

async def check_setup():
    lk = api.LiveKitAPI(
        'https://relatim-v1wlyfls.livekit.cloud',
        'APIgNUtuSTugMPF',
        'G94A3JBc7teQiXnmvA2RO1MTQWRf7FRa7XfWYJCebJAB'
    )
    
    print('=== LiveKit Setup Check ===\n')
    
    # Check rooms
    try:
        rooms = await lk.room.list_rooms(api.ListRoomsRequest())
        print('Active Rooms:')
        if rooms.rooms:
            for room in rooms.rooms:
                print(f'  - {room.name} ({room.num_participants} participants)')
        else:
            print('  (none)')
    except Exception as e:
        print(f'  Error: {e}')
    
    # Check SIP dispatch rules
    print('\nSIP Dispatch Rules:')
    try:
        rules = await lk.sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
        if rules.items:
            for rule in rules.items:
                print(f'  - ID: {rule.sip_dispatch_rule_id}')
                print(f'    Name: {rule.name}')
        else:
            print('  (none - you may need to create one!)')
    except Exception as e:
        print(f'  Error: {e}')
    
    await lk.aclose()

asyncio.run(check_setup())
