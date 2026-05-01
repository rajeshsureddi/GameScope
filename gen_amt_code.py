from jinja2 import Environment, FileSystemLoader
import pandas as pd
import argparse

""" 
python3 gen_amt_code.py --env sandbox --use_github --train_csv train_vids.csv --sample_csv sample_vids.csv --gold_csv gold_vids.csv --hit_csv hit_test.csv --backup_csv backup_test.csv
"""
def gen_html_code(args):
    '''
    Generate HTML code for the crowdsourced video study.
    '''
    print(f'Environment: {args.env}')

    with open('amt/template.htm') as template_file:
        template_str = template_file.read()
    template = Environment(loader=FileSystemLoader("amt/")).from_string(template_str)

    debug = (args.env == 'local')  # If False, use ${videos1}

    # Set HIT parameters.
    # If env is 'local' or 'sandbox', small values are used for debugging.
    # if args.env in ['local', 'sandbox']:
    #     n_repeat = 1  # Number of videos being repeated
    #     n_golden = 2  # Number of golden videos with known MOS
    #     n_labels = 3  # Number of videos to be labelled
    #     n_backup = 10
    if args.env in ['local', 'sandbox']:
        n_repeat = 6  # Number of videos being repeated
        n_golden = 4  # Number of golden videos with known MOS
        n_labels = 31  # Number of videos to be labelled
        n_backup = 10
    # Values for a "full" HIT - customize as required.
    elif args.env == 'lab_sandbox':
        n_repeat = 0  # Trusted subjects, do not repeat
        n_golden = 0  # Trusted subjects, do not test against gold
        n_labels = 217  # Long session because of trusted subjects
        n_backup = 10
    else:
        n_repeat = 5  # Number of videos being repeated
        n_golden = 5  # Number of golden videos with known MOS
        n_labels = 84  # Number of videos to be labelled
        n_backup = 10

    n_trains = 4
    n_samples = 5

    # max_duration_ms = 18000  # 18s
    max_duration_ms = -1 # 18s
    max_loading_time = 20000

    base_aws_url = 'https://gaming-vqa.s3.us-east-2.amazonaws.com/example-samples/'
    base_github_url = 'https://gaming-vqa.s3.us-east-2.amazonaws.com/example-samples/'


    # Load list of training videos from CSV
    df = pd.read_csv(args.train_csv)
    train_vids = [(base_github_url if args.use_github else base_aws_url) + vid_path + '.mp4' + ('?raw=true' if args.use_github else '') for vid_path in df['train_vids'].tolist()]
    print(train_vids)

    # sample videos
    df = pd.read_csv(args.sample_csv)
    # sample_vids = df['sample_vids'].tolist()
    sample_vids = [(base_github_url if args.use_github else base_aws_url) + vid_path + '.mp4' + ('?raw=true' if args.use_github else '') for vid_path in df['sample_vids'].tolist()]
    print(sample_vids)

    # Load list of HIT videos from CSV if provided.
    if args.hit_csv:
        df = pd.read_csv(args.hit_csv)
        # df.drop('Unnamed: 0', axis=1, inplace=True)
        # label_vids = df.iloc[args.hit_id].tolist()
        label_vids = [(base_github_url if args.use_github else base_aws_url) + vid_path + '.mp4'+ ('?raw=true' if args.use_github else '') for vid_path in df.iloc[args.hit_id].tolist()]
    elif debug:
        # Force HIT CSV to be provided when env is 'local'
        raise OSError('Must provide HIT CSV when env is \'local\'')
    else:
        label_vids = ['${videos' + str(i) + '}' for i in range(1, n_labels+1)]
    print(label_vids)

    if args.backup_csv:
        df = pd.read_csv(args.backup_csv)
        # backup_vids = df['backup_vids'].tolist()
        backup_vids = [base_aws_url + vid_path + '.mp4' for vid_path in df['backup_vids'].tolist()]
    elif debug:
        # Force Backup CSV to be provided when env is 'local'
        raise OSError('Must provide Backup CSV when env is \'local\'')
    else:
        backup_vids = ['${videos' + str(i) + '}' for i in range(n_labels+1, n_labels+n_backup+1)]
    print(backup_vids)

    # Load list of Gold videos from CSV if provided.
    if args.gold_csv:
        df = pd.read_csv(args.gold_csv)
        gold_vids = [(base_github_url if args.use_github else base_aws_url) + vid_path + '.mp4' + ('?raw=true' if args.use_github else '') for vid_path in df['gold_vids'].tolist()]
    elif debug:
        # Force HIT CSV to be provided when env is 'local'
        raise OSError('Must provide Gold CSV when env is \'local\'')
    else:
        gold_vids = ['${videos' + str(i) + '}' for i in range(n_labels+n_backup+1, n_labels+n_backup+n_golden+1)]
    print(gold_vids)

    if args.debug_broken:
        label_vids = ['broken1', 'broken2', 'broken3'] + label_vids
        gold_vids = ['brokenGold'] + gold_vids

    demo_img_mobile_url = 'https://gaming-vqa.s3.us-east-2.amazonaws.com/example-samples/amt_intro/intro_examples/gaming_vqa_a.png'
    demo_img_desktop_url = 'https://gaming-vqa.s3.us-east-2.amazonaws.com/example-samples/amt_intro/intro_examples/gaming_vqa_a.png'
    # demo_img_mobile_url = 'https://raw.githubusercontent.com/tmvideostudy/content/main/slider_demo.png'
    # demo_img_desktop_url = 'https://raw.githubusercontent.com/tmvideostudy/content/main/slider_demo.png'
    gold_vids = gold_vids[:n_golden]
    train_vids = train_vids[:n_trains]
    sample_vids = sample_vids[:n_samples]
    # base_url = 'https://drive.google.com/uc?export=view&id='

    template_kwargs = {
        'debug': debug,
        'maxLoadingTime': max_loading_time,  # (seconds) longest loading time allowed for training session
        'help': True,
        'maxDurationMs': max_duration_ms,  # Set to -1 to disable timeout feature. User can click "I didn't see the video".
        'n_repeat': n_repeat,
        'useBackupVids': True,
        'checkdistance': True,
        'showprogress': True,
        'fullscreen': False,  # set to True to play in full screen - True is currently broken
        'baseUrl': base_aws_url,
        'baseGoldUrl': (base_github_url if args.use_github else base_aws_url),
        'demoImgMobileUrl': demo_img_mobile_url,
        'demoImgDesktopUrl': demo_img_desktop_url,
        'sampleVids': sample_vids,
        'trainVids': train_vids,
        'goldVids': gold_vids,
        'labelVids': label_vids,
        'backupVids': backup_vids
    }

    print('Template args:')
    for key in template_kwargs:
        print(f'{key} = {template_kwargs[key]}')

    rendered = template.render(**template_kwargs)

    if args.out_file is None:
        args.out_file = f'{args.env}_rendered.htm'

    with open(args.out_file, 'w') as out_file:
        out_file.write(rendered)


def main():
    parser = argparse.ArgumentParser(description='Generate HTML code for AMT')
    parser.add_argument('--env', help='Environment for which code is to be generated', type=str, required=True, choices=['local', 'sandbox', 'lab_sandbox', 'amt'])
    parser.add_argument('--use_github', help='Flag to use GitHub for high-access videos', action='store_true', default=False)
    parser.add_argument('--train_csv', help='Path to CSV file containing training videos', type=str, required=True)
    parser.add_argument('--sample_csv', help='Path to CSV file containing sample videos', type=str, required=True)
    parser.add_argument('--gold_csv', help='Path to CSV file containing golden videos', type=str, required=False, default=None)
    parser.add_argument('--hit_csv', help='Path to CSV file containg videos in each HIT. Required when env is \'local\'', type=str, required=False, default=None)
    parser.add_argument('--backup_csv', help='Path to CSV file containg backup videos. Required when env is \'local\'', type=str, required=False, default=None)
    parser.add_argument('--hit_id', help='Row of HIT from HIT CSV to use. Default: 0', type=int, required=False, default=0)
    parser.add_argument('--debug_broken', help='Debug the logic that handles broken videos. Only allowed when env is not \'amt\'', action='store_true', default=False)
    parser.add_argument('--out_file', help='Output HTML path. Default: sandbox_rendered.htm (or similarly named file for each --env value) at repo root.', type=str, default=None)
    args = parser.parse_args()
    gen_html_code(args)


if __name__ == '__main__':
    main()
