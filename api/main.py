from fastapi import FastAPI, HTTPException, Query
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from sim_entry_points.traverse_api_input import traverse_api_input
from . import db
from . import read_helpers

app = FastAPI()

# CORS - copy origins from the Flask app
origins = [
    "http://localhost:3000",
    "https://fgocif.jjbly.uk",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimRequest(BaseModel):
    Team: list
    Mystic_Code_ID: int
    Quest_ID: int
    Commands: list


@app.post("/simulate")
async def simulate(req: SimRequest):
    # Run simulation synchronously — simulations are very fast (<0.5s)
    try:
        result = traverse_api_input(
            req.Team,
            req.Mystic_Code_ID,
            req.Quest_ID,
            req.Commands,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"result": result}


@app.get('/api/servants')
async def get_servants(rarity: Optional[List[int]] = Query(None), className: Optional[str] = '', npType: Optional[str] = '', attackType: Optional[str] = '', search: Optional[str] = '', team: Optional[List[int]] = Query(None)):
    # Build query similar to Flask
    query = {'$and': []}

    if rarity:
        query['$and'].append({'rarity': {'$in': [int(r) for r in rarity]}})
    if className:
        class_list = className.split(',') if className else []
        if class_list:
            query['$and'].append({'className': {'$in': class_list}})
    if npType:
        np_list = npType.split(',') if npType else []
        if np_list:
            query['$and'].append({'noblePhantasms.card': {'$in': np_list}})
    if attackType:
        attack_list = attackType.split(',') if attackType else []
        if attack_list:
            query['$and'].append({'noblePhantasms.effectFlags': {'$in': attack_list}})
    if search:
        query['$and'].append({'name': {'$regex': search, '$options': 'i'}})

    if not query['$and']:
        query = {}

    servants = list(db.servants_collection.find(query, {
        '_id': 0,
        'id': 1,
        'name': 1,
        'collectionNo': 1,
        'className': 1,
        'rarity': 1,
        'noblePhantasms.card': 1,
        'noblePhantasms.effectFlags': 1,
        'extraAssets.faces.ascension.4': 1
    }))

    if team:
        team_collection_nos = [int(no) for no in team]
        filtered_servants = [servant for servant in servants if servant.get('collectionNo') not in team_collection_nos]
    else:
        filtered_servants = servants

    return filtered_servants


@app.get('/api/servants/{collectionNo}')
async def get_servant_by_collectionNo(collectionNo: int):
    try:
        servant = db.servants_collection.find_one({'collectionNo': collectionNo}, {
            '_id': 0,
            'id': 1,
            'name': 1,
            'collectionNo': 1,
            'className': 1,
            'rarity': 1,
            'noblePhantasms.card': 1,
            'noblePhantasms.effectFlags': 1,
            'extraAssets.faces.ascension.4': 1
        })
        if servant:
            return servant
        else:
            raise HTTPException(status_code=404, detail='Servant not found')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/mysticcodes')
async def get_mysticcodes():
    mysticcodes = list(db.mysticcode_collection.find({}, {
        '_id': 0,
        'id': 1,
        'name': 1,
        'extraAssets.item.male': 1
    }))
    return mysticcodes


@app.get('/api/mysticcodes/{mysticcode_id}')
async def get_mysticcodes_by_id(mysticcode_id: int):
    # Query the database by id
    mysticcode = list(db.mysticcode_collection.find({'id': mysticcode_id}, {
        '_id': 0,
        'id': 1,
        'name': 1,
        'extraAssets.item.male': 1
    }))
    return mysticcode


@app.get('/api/quests')
async def get_quests(warLongNames: Optional[List[str]] = Query(None), recommendLv: Optional[str] = ''):
    try:
        query = {'$and': []}
        if warLongNames:
            query['$and'].append({'warLongName': {'$in': warLongNames}})
        if recommendLv:
            query['$and'].append({'recommendLv': recommendLv})
        if not query['$and']:
            query = {}
        quests = list(db.quests_collection.find(query, {
            '_id': 0,
            'name': 1,
            'warLongName': 1,
            'id': 1,
            'recommendLv': 1,
            'stages': 1,
        }))
        if not quests:
            raise Exception('No quests found in the database')
        return quests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/quests/warLongNames')
async def get_quests_warLongNames():
    try:
        warLongNames = db.quests_collection.distinct('warLongName')
        if not warLongNames:
            raise Exception('No warLongNames found in the database')
        return warLongNames
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/quests/filter')
async def get_filtered_quests(warLongNames: Optional[List[str]] = Query(None), recommendLv: Optional[str] = ''):
    try:
        match_stage = {}
        project_stage = {
            '$project': {
                '_id': 0,
                'name': 1,
                'warLongName': 1,
                'id': 1,
                'recommendLv': 1,
                'stages': {
                    '$map': {
                        'input': '$stages',
                        'as': 'stage',
                        'in': {
                            'enemies': {
                                '$cond': {
                                    'if': {'$isArray': '$$stage.enemies'},
                                    'then': '$$stage.enemies',
                                    'else': []
                                }
                            }
                        }
                    }
                }
            }
        }

        if warLongNames:
            match_stage['warLongName'] = {'$in': warLongNames}
        if recommendLv:
            match_stage['recommendLv'] = recommendLv

        if not match_stage:
            pipeline = [project_stage]
        else:
            pipeline = [{'$match': match_stage}, project_stage]

        quests = list(db.quests_collection.aggregate(pipeline))

        if not quests:
            raise Exception('No quests found in the database')
        return quests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/data')
async def get_data():
    log_file = os.path.join('FGO-can-it-farm', 'outputs', 'output.log')
    output_file = os.path.join('FGO-can-it-farm', 'outputs', 'output.md')

    logs = read_helpers.read_file(log_file)
    output_md = read_helpers.read_file(output_file)

    summary, success_count, failure_count, results = read_helpers.summarize_execution(logs, output_md)

    data = {
        'summary': summary,
        'success_count': success_count,
        'failure_count': failure_count,
        'results': results,
        'logs': logs,
        'output_md': output_md
    }

    return data
