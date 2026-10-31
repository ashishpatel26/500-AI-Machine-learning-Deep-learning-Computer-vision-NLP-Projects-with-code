# Experiment 1 -- Git Bash and GitHub

## Aim

Initialize a Git repository for a data science project, push it to
GitHub, create Python programs, create a branch, and demonstrate
differences between the default branch (`main`) and `GIT-EXAM`.

## Requirements

-   Git and Git Bash installed
-   Python installed
-   GitHub account
-   Internet connection

## Important before starting

1.  Create an **empty** GitHub repository named `Data-Science-Project`
    at https://github.com/new. Do not add a README, `.gitignore`, or
    license on GitHub.
2.  Replace `YOUR-USERNAME` and `your-email@gmail.com` below with your
    own details.
3.  These instructions use `main` as the default branch. If your
    instructor's repository uses `master`, replace `main` with `master`
    in the branch-comparison commands.

## Part A -- Create and push the first program on main

### 1. Check installations

``` bash
git --version
python --version
```

If `python` is not recognized, try `python3 --version` and use `python3`
to run programs.

### 2. Create the project folder and initialize Git

``` bash
mkdir Data-Science-Project
cd Data-Science-Project
git init
git status
```

### 3. Configure your Git identity

``` bash
git config --global user.name "Your Name"
git config --global user.email "your-email@gmail.com"
git config --global --list
```

### 4. Connect the local repository to GitHub

``` bash
git remote add origin https://github.com/YOUR-USERNAME/Data-Science-Project.git
git remote -v
```

If you accidentally added the wrong URL, correct it with:

``` bash
git remote set-url origin https://github.com/YOUR-USERNAME/Data-Science-Project.git
```

### 5. Create `program1.py` -- multiplication table

``` bash
cat > program1.py <<'EOF'
num = int(input("Enter a number: "))

for i in range(1, 11):
    print(num, "x", i, "=", num * i)
EOF
```

Run it:

``` bash
python program1.py
```

Example: entering `5` prints the multiplication table from `5 x 1 = 5`
through `5 x 10 = 50`.

### 6. Add, commit, and push

``` bash
git add program1.py
git status
git commit -m "Add multiplication table program"
git branch -M main
git push -u origin main
```

Open your GitHub repository in a browser and refresh. Confirm that
`program1.py` is visible.

## Part B -- Create and push GIT-EXAM branch

### 7. Create and switch to the new branch

``` bash
git switch -c GIT-EXAM
git branch
```

The asterisk (`*`) should appear next to `GIT-EXAM`.

Older Git versions can use:

``` bash
git checkout -b GIT-EXAM
```

### 8. Create `program2.py` -- greatest of two numbers

The PDF says to create a file named `program2`. Use the `.py` extension
so it is clearly a Python source file.

``` bash
cat > program2.py <<'EOF'
a = int(input("Enter first number: "))
b = int(input("Enter second number: "))

if a > b:
    print("Greatest number is:", a)
elif b > a:
    print("Greatest number is:", b)
else:
    print("Both numbers are equal")
EOF
```

Run it:

``` bash
python program2.py
```

### 9. Commit and push the branch

``` bash
git add program2.py
git status
git commit -m "Add greatest of two numbers program"
git push -u origin GIT-EXAM
```

Refresh GitHub. Use the branch selector to view `GIT-EXAM` and confirm
that `program2.py` appears there.

## Part C -- Demonstrate the difference between branches

### 10. List branches

``` bash
git branch
```

Expected: `main` and `GIT-EXAM`; the current branch has `*`.

### 11. Compare files/commits

Show commits that are on `GIT-EXAM` but not on `main`:

``` bash
git log --oneline main..GIT-EXAM
```

Show the file changes introduced by the branch:

``` bash
git diff --name-status main..GIT-EXAM
```

Expected: `program2.py` is listed as an added file (`A`).

To view the actual code difference:

``` bash
git diff main..GIT-EXAM
```

### 12. Switch between branches and verify file presence

``` bash
git switch main
ls
```

On `main`, you should see `program1.py`, but not `program2.py`.

``` bash
git switch GIT-EXAM
ls
```

On `GIT-EXAM`, you should see both `program1.py` and `program2.py`.

## Expected final repository structure

``` text
Data-Science-Project/
├── program1.py
└── program2.py   # present on GIT-EXAM branch; not on main
```

## Common errors and fixes

  ------------------------------------------------------------------------------------------
  Error / situation                       Fix
  --------------------------------------- --------------------------------------------------
  `git: command not found`                Install Git for Windows and reopen Git Bash.

  `python: command not found`             Try `python3 --version`; install Python and enable
                                          PATH if needed.

  `remote origin already exists`          Run
                                          `git remote set-url origin YOUR-REPOSITORY-URL`.

  `src refspec main does not match any`   Make sure you created a commit, then check
                                          `git branch`.

  Authentication failed                   Complete the browser sign-in / Git Credential
                                          Manager prompt. GitHub account passwords are not
                                          accepted for Git HTTPS authentication.

  `nothing to commit`                     Run `git status`; check that the file was saved
                                          and is inside the repository folder.

  Branch already exists                   Run `git switch GIT-EXAM` instead of creating it
                                          again.
  ------------------------------------------------------------------------------------------

## Viva questions and short answers

1.  **What is Git?** Git is a distributed version control system used to
    track changes in files.
2.  **What is GitHub?** GitHub is an online platform for hosting Git
    repositories and collaborating.
3.  **What is a repository?** A repository is a project folder whose
    changes are tracked by Git.
4.  **What does `git init` do?** It initializes a new local Git
    repository.
5.  **What is a commit?** A commit is a saved snapshot of tracked
    project changes.
6.  **What does `git add` do?** It stages changes for the next commit.
7.  **What does `git push` do?** It sends local commits to a remote
    repository.
8.  **What is a branch?** A branch is an independent line of
    development.
9.  **What does `git switch -c GIT-EXAM` do?** It creates the branch and
    switches to it.
10. **What does `git diff main..GIT-EXAM` show?** It shows differences
    between the two branch tips.
11. **What is `origin`?** It is the conventional short name for the
    remote repository.
12. **Why use branches?** To develop features separately without
    immediately changing the main branch.

## Practical completion checklist

-   [ ] Git and Python versions checked
-   [ ] Empty GitHub repository created
-   [ ] Local repository initialized
-   [ ] Remote `origin` configured
-   [ ] `program1.py` created, run, committed, and pushed on `main`
-   [ ] `GIT-EXAM` branch created
-   [ ] `program2.py` created and run
-   [ ] Branch committed and pushed
-   [ ] GitHub remote checked
-   [ ] Difference between `main` and `GIT-EXAM` demonstrated

**Exam tip:** Run commands one at a time. After each major stage, use
`git status` or `git branch` to verify your current state. Do not paste
placeholder values such as `YOUR-USERNAME` literally.
